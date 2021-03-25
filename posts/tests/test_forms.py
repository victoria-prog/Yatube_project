import shutil

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()

TEST_DIR = 'test_data'


@override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='clapathy')
        cls.group = Group.objects.create(
            title='Лев',
            description='Описание группы',
            slug='lev'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_DIR)
        super().tearDownClass()

    def setUp(self):
        # создаем авторизованного пользователя
        self.user = PostCreateFormTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_new_post(self):
        """Валидная форма создает запись в Post."""
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'group': PostCreateFormTests.group.id,
            'text': 'Текст из формы',
            'image': uploaded
        }
        form_text = form_data['text']
        form_image = form_data['image']
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        new_post = Post.objects.get(
            text=form_text,
            group_id=PostCreateFormTests.group.id
        )
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(new_post.group_id, PostCreateFormTests.group.id)
        self.assertEqual(new_post.text, form_text)
        self.assertEqual(new_post.image, f'posts/{form_image}')

    def test_cant_create_form_with_no_text(self):
        """Отсутствие текста в поле text не создает запись в Post."""
        post_count = Post.objects.count()
        form_data = {
            'group': PostCreateFormTests.group.id,
            'text': '',
        }
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        old_post = Post.objects.get(
            text=PostCreateFormTests.post.text,
            group_id=PostCreateFormTests.group.id
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(PostCreateFormTests.group.id, old_post.group_id)
        self.assertEqual(PostCreateFormTests.post.text, old_post.text)
        self.assertFormError(
            response, 'form', 'text', 'Обязательное поле.'
        )
        self.assertEqual(response.status_code, 200)

    def test_update_post(self):
        """Валидная форма обновляет запись в Post."""
        post_count = Post.objects.count()
        form_data = {
            'group': PostCreateFormTests.group.id,
            'text': 'Изменен',
        }
        form_text = form_data['text']
        old_post = Post.objects.get(
            text=PostCreateFormTests.post.text,
            group_id=PostCreateFormTests.group.id
        )
        response = self.authorized_client.post(
            reverse('post_edit', kwargs={
                'username': PostCreateFormTests.user,
                'post_id': PostCreateFormTests.post.id
            }),
            data=form_data, follow=True
        )
        upd_post = Post.objects.get(
            text=form_text, group_id=PostCreateFormTests.group.id
        )
        group_posts = Post.objects.filter(group=PostCreateFormTests.group.id)
        self.assertRedirects(response, reverse('post', kwargs={
            'username': PostCreateFormTests.user,
            'post_id': PostCreateFormTests.post.id
        }))
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(PostCreateFormTests.group.id, upd_post.group_id)
        self.assertEqual(form_text, upd_post.text)
        self.assertNotEqual(old_post.text, group_posts[0].text)
