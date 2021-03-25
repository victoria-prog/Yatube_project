from django.contrib.auth import get_user_model
from django.test import Client, TestCase
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
        cls.commt = f'/{PostURLTests.username}/{PostURLTests.post.id}/comment'

    def setUp(self):
        self.guest_client = Client()
        self.user = PostURLTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    # Проверяем доступность страниц для любого пользователя
    def test_urls_at_desired_location(self):
        """Страницы '/', '/group/<slug>/ , /<username>/,
        /<username>/<post_id>/ доступны любому пользователю.
        Несуществующая страница возвращает код ошибки 404.
        """
        url_adresses = {
            PostURLTests.indx_url: 200,
            PostURLTests.group_url: 200,
            PostURLTests.usr_url: 200,
            PostURLTests.usr_id_url: 200,
            '/wrong/': 404
        }
        for adress, status_code in url_adresses.items():
            with self.subTest():
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, status_code)

    # Проверяем доступность страниц для авторизованного пользователя
    def test_urls_for_authorized_client_exists_at_desired_location(self):
        """Страницы '/', '/group/<slug>/, '/new/' доступны авторизованному
        пользователю. Страница /<username>/<post_id>/edit/ доступна автору
        поста"""
        url_adresses = {
            PostURLTests.indx_url: 200,
            PostURLTests.group_url: 200,
            PostURLTests.new_url: 200,
            PostURLTests.edit_url: 200
        }
        for adress, status_code in url_adresses.items():
            with self.subTest():
                response = self.authorized_client.get(adress)
                self.assertEqual(response.status_code, status_code)

    # Проверяем редиректы для неавторизованного пользователя и не автора поста
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
        redirect_comment = self.guest_client.get(PostURLTests.commt)
        self.assertRedirects(
            redirect_new, f'/auth/login/?next={PostURLTests.new_url}'
        )
        self.assertRedirects(
            redirect_anon,
            f'/auth/login/?next=/'
            f'{PostURLTests.username}/{PostURLTests.post.id}/edit/'
        )
        self.assertRedirects(
            redirect_comment, f'/auth/login/?next={PostURLTests.commt}'
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
