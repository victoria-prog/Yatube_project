from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД для проверки доступности адреса '/group/<slug>/'
        cls.group = Group.objects.create(
            title='Тест группа',
            slug='test-slug',
            description='Группа любителей книг'
        )
        cls.test_slug = cls.group.slug
        cls.user = User.objects.create_user('clapathy')
        cls.username = cls.user.username
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group
        )
        cls.user_non_author = User.objects.create_user('vika')
        cls.indx_url, cls.new_url, cls.group_url, cls.usr_url, cls.edit_url = (
            '/',
            '/new/',
            f'/group/{PostURLTests.test_slug}/',
            f'/{PostURLTests.username}/',
            f'/{PostURLTests.username}/{PostURLTests.post.id}/edit/',
        )
        cls.usr_id_url = f'/{PostURLTests.username}/{PostURLTests.post.id}/'

    def setUp(self):
        self.guest_client = Client()
        self.user = PostURLTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    # Проверяем доступность страниц для любого пользователя
    def test_urls_at_desired_location(self):
        """Страницы '/', '/group/<slug>/ , /<username>/,
        /<username>/<post_id>/ доступны любому пользователю.
        """
        url_adresses = [
            PostURLTests.indx_url,
            PostURLTests.group_url,
            PostURLTests.usr_url,
            PostURLTests.usr_id_url,
        ]
        for adress in url_adresses:
            with self.subTest():
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_for_authorized_client_exists_at_desired_location(self):
        """Страницы '/', '/group/<slug>/, '/new/' доступны авторизованному
        пользователю. Страница /<username>/<post_id>/edit/ доступна автору
        поста"""
        url_adresses = [
            PostURLTests.indx_url,
            PostURLTests.group_url,
            PostURLTests.new_url,
            PostURLTests.edit_url
        ]
        for adress in url_adresses:
            with self.subTest():
                response = self.authorized_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_does_not_exist_at_wrong_page(self):
        """Страница с неверным адресом возвращает ошибку 404"""
        wrong_adress = '/wrong/'
        response = self.authorized_client.get(wrong_adress)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_url_new_redirect_anonymous_on_admin_login(self):
        """Страница по адресу '/new/' и '/<username>/<post_id>/comment'
        перенаправит анонимного пользователя на страницу логина.
        Страница /<username>/<post_id>/edit/ перенаправит анонимного
        пользователя и не автора поста  на страницу поста."""
        self.user_non_athor = PostURLTests.user_non_author
        self.authoriz_client2 = Client()
        self.authoriz_client2.force_login(self.user_non_athor)
        redirect_new = self.guest_client.get(
            PostURLTests.new_url, follow=True
        )
        redirect_anon = self.guest_client.get(PostURLTests.edit_url)
        redirect_non_author = self.authoriz_client2.get(PostURLTests.edit_url)
        reversed_login = reverse('login')
        reversed_post = reverse('new_post')
        self.assertRedirects(
            redirect_new, f'{reversed_login}?next={reversed_post}'
        )
        kw_edit = {
            'username': PostURLTests.username, 'post_id': PostURLTests.post.id
        }
        reversed_login = reverse('login')
        reversed_edit = reverse('post_edit', kwargs=kw_edit)
        self.assertRedirects(
            redirect_anon,
            f'{reversed_login}?next={reversed_edit}'
        )
        self.assertRedirects(redirect_non_author, PostURLTests.usr_id_url)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            PostURLTests.indx_url: 'posts/index.html',
            PostURLTests.group_url: 'posts/group.html',
            PostURLTests.new_url: 'posts/new_post.html',
            PostURLTests.edit_url: 'posts/new_post.html'
        }
        for adress, template in templates_url_names.items():
            with self.subTest():
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)
