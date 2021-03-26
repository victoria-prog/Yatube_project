import textwrap

from django.contrib.auth import get_user_model
from django.test import TestCase
from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Группа любителей книг'
        )
        cls.user = User.objects.create_user(username='clapathy')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user
        )

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст',
            'group': 'Группа',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Напишите текст',
            'group': 'Выберите группу',
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)

    def test_group_and_post_instance_is_title_field(self):
        """В поле __str__  объекта group записано значение поля group.title.
        В поле __str__  объекта post записано значение поля post.text."""
        group, post = PostModelTest.group, PostModelTest.post
        title_view = {
            PostModelTest.group: group.title,
            PostModelTest.post: textwrap.shorten(post.text, (15))
        }
        for value, expected in title_view.items():
            with self.subTest(value=value):
                self.assertEqual(str(value), expected)
