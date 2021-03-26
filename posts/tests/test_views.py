import shutil
from http import HTTPStatus

from django import forms
from django.contrib import auth
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comment, Follow, Group, Post

User = get_user_model()

TEST_DIR = 'test_data'


@override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.small_giff = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.giff',
            content=cls.small_giff,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Заголовок',
            description='Описание',
            slug='my-slug',
        )
        cls.group_2 = Group.objects.create(
            title='Лев Толстой',
            description='Группа любителей книг',
            slug='lev-tolstoy',
        )
        cls.author = User.objects.create_user(username='lev')
        cls.post_author = Post.objects.create(
            author=cls.author,
            text='Текст от автора leo',
            group=PostPagesTests.group,
        )
        cls.user = User.objects.create_user(username='clapathy')
        cls.username = cls.user.username
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст',
            group=cls.group,
            image=cls.uploaded
        )
        

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_DIR)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.user = PostPagesTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def check_context_is_correct(self, context):
        """Вспомогательный метод проверки контекста"""
        for value, expected in context.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        test_slug = PostPagesTests.group.slug
        templates_page_names = {
            'posts/index.html': reverse('index'),
            'posts/group.html': reverse('group', kwargs={'slug': test_slug}),
            'posts/new_post.html': reverse('new_post'),
            'about/author.html': reverse('about:author'),
            'about/tech.html': reverse('about:tech')
        }
        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    # Проверяем, что используется правильный контекст
    def test_create_page_show_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.FileField
        }
        url_adresses = {
            reverse('new_post'): form_fields,
            reverse(
                'post_edit', kwargs={
                    'username': PostPagesTests.username,
                    'post_id': PostPagesTests.post.id
                }
            ): form_fields
        }
        for reverse_name, value in url_adresses.items():
            for field, expected in form_fields.items():
                with self.subTest(reverse_name=reverse_name):
                    response = self.authorized_client.get(reverse_name)
                    form_field = response.context['form'].fields[field]
                    self.assertIsInstance(form_field, expected)

    def test_index_follow_index_and_profile_page_show_correct_context(self):
        """Шаблоны 'index', 'profile', 'follow_index' сформированы с правильным
        контекстом. При указании группы на главной странице отображается пост.
        Новая запись пользователя появляется в ленте тех, кто на него подписан.
        """
        responses = {
            'resp_profile': self.guest_client.get(
                reverse('profile', kwargs={
                    'username': PostPagesTests.username
                })
            ),
            'resp_index': self.guest_client.get(reverse('index')),
        }
        for adress, resp in responses.items():
            first_object = resp.context['post_list'][0]
            context = {
                first_object.text: PostPagesTests.post.text,
                first_object.author.username: PostPagesTests.username,
                first_object.group.slug: PostPagesTests.group.slug,
                first_object.image: PostPagesTests.post.image
            }
            self.check_context_is_correct(context)

    def test_group_page_show_correct_context(self):
        """Шаблон 'group' сформирован с правильным контекстом.
        При указании группы на странице 'group' отображается пост.
        В других группах пост не отображается.
        """
        response = self.guest_client.get(
            reverse('group', kwargs={'slug': PostPagesTests.group.slug})
        )
        response_for_another_grp = self.guest_client.get(
            reverse('group', kwargs={'slug': PostPagesTests.group_2.slug})
        )
        exp_group2_count = PostPagesTests.group_2.posts.count()
        group2_count = response_for_another_grp.context['group_posts'].count()
        group = response.context['group']
        group_first_obj = response.context['group_posts'][0]
        group_context = {
            group.title: PostPagesTests.group.title,
            group.description: PostPagesTests.group.description,
            group.slug: PostPagesTests.group.slug,
            group2_count: exp_group2_count,
            group_first_obj.text: PostPagesTests.post.text,
            group_first_obj.image: PostPagesTests.post.image
        }
        self.check_context_is_correct(group_context)

    def test_post_page_show_correct_context(self):
        """Шаблон 'post' сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('post', kwargs={
                'username': PostPagesTests.username,
                'post_id': PostPagesTests.post.id
            })
        )
        post = response.context['post']
        post_context = {
            post.text: PostPagesTests.post.text,
            post.author: PostPagesTests.post.author,
            post.group.slug: PostPagesTests.group.slug,
            post.image: PostPagesTests.post.image
        }
        self.check_context_is_correct(post_context)

    def test_check_cache_at_index_page(self):
        """Проверка кэша главной страницы"""
        response = self.guest_client.get(reverse('index'))
        Post.objects.create(
            text='Новый текст',
            author=PostPagesTests.user,
        )
        second_response = self.guest_client.get(reverse('index'))
        self.assertEqual(response.content, second_response.content)
        cache.clear()
        response_after_clear_cache = self.guest_client.get(reverse('index'))
        self.assertNotEqual(
            second_response.content, response_after_clear_cache.content
        )

    def test_authorized_user_can_folow(self):
        """Авторизованный пользователь может подписываться
        на других пользователей"""
        follow_count = Follow.objects.count()
        self.authorized_client.get(reverse('profile_follow', kwargs={
            'username': PostPagesTests.author.username
        }))
        self.assertEqual(Follow.objects.count(), follow_count + 1)

    def test_authorized_user_can_unfolow(self):
        """Авторизованный пользователь может отписываться
        от других пользователей"""
        follow_count = Follow.objects.count()
        Follow.objects.create(
            user=PostPagesTests.user,
            author=PostPagesTests.author
        )
        self.authorized_client.get(reverse('profile_unfollow', kwargs={
            'username': PostPagesTests.author.username
        }))
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_new_post_shown_for_follower(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан."""
        Follow.objects.create(
            user=PostPagesTests.user,
            author=PostPagesTests.author
        )
        response = self.authorized_client.get(reverse('follow_index'))
        first_post = response.context['favor_posts'][0]
        self.assertEqual(first_post.text, PostPagesTests.post_author.text)
        self.assertEqual(first_post.author, PostPagesTests.post_author.author)
        self.assertEqual(first_post.group, PostPagesTests.post_author.group)

    def test_new_post_not_shown_for_follower(self):
        """Новая запись пользователя не появляется в ленте тех,
        кто на него не подписан."""
        Post.objects.create(
            author=PostPagesTests.author,
            text='Новый пост',
            group=PostPagesTests.group,
        )
        response = self.authorized_client.get(reverse('follow_index'))
        count_favorite_post = response.context['favor_posts'].count()
        self.assertEqual(count_favorite_post, 0)

    def test_non_authorised_cannot_comment_post(self):
        """Неавторизванный пользователь не может комментировать посты"""
        kw = {
           'username': PostPagesTests.username,
           'post_id': PostPagesTests.post.id
        }
        response = self.guest_client.get(
            f"{reverse('add_comment', kwargs=kw)}"
        )
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('add_comment', kwargs=kw)}"
        )

    def test_authorised_can_comment_post(self):
        """Авторизванный пользователь может комментировать посты"""
        kw = {
           'username': PostPagesTests.username,
           'post_id': PostPagesTests.post.id
        }
        response = self.authorized_client.get(
            f"{reverse('add_comment', kwargs=kw)}"
        )
        self.assertEqual(response.status_code, HTTPStatus.OK.value)
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Комментарий',
        }
        response = self.authorized_client.post(
            reverse('add_comment', kwargs=kw),
            data=form_data,
            follow=True
        )
        self.assertEqual(comment_count + 1, Comment.objects.count())


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='clapathy')
        cls.username = cls.user.username
        # создаем 13 записей в базе данных
        Post.objects.bulk_create(
            [Post(text=f'Текст {post}', author=cls.user) for post in range(13)]
        )

    def setUp(self):
        # создаем неавторизованного пользователя
        self.guest_client = Client()

    def test_first_page_containse_ten_records(self):
        """Первая страница содержит 10 записей."""
        response = self.guest_client.get(reverse('index'))
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_second_page_containse_three_records(self):
        """Вторая страница содержит 3 записи."""
        response = self.guest_client.get(reverse('index') + '?page=2')
        self.assertEqual(len(response.context.get('page').object_list), 3)

    def test_first_page_show_correct_context(self):
        """Шаблон 'index' c 10 постами на странице
        сформирован с правильным контекстом.
        """
        comment = Comment
        response = self.guest_client.get(reverse('index'))
        all_object_at_first_page = response.context['page'].object_list
        for index, post in zip(range(12, 2, -1), all_object_at_first_page):
            test_text = f'Текст {index}'
            self.assertEqual(post.text, test_text)
            self.assertEqual(
                post.author.username, PaginatorViewsTest.username
            )
