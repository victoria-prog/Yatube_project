from django.test import Client, TestCase
from django.urls import reverse


class AboutViewTests(TestCase):

    def setUp(self):
        self.guest_client = Client()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_page_names = {
            'about/author.html': reverse('about:author'),
            'about/tech.html': reverse('about:tech'),
        }
        # Проверяем, что при обращении к name
        # вызывается соответствующий HTML-шаблон
        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_and_profile_page_show_correct_context(self):
        """Шаблоны 'author' и 'tech' сформированы с правильным контекстом."""
        response_author = self.guest_client.get(reverse('about:author'))
        response_tech = self.guest_client.get(reverse('about:tech'))
        self.assertIn('Об авторе проекта', response_author.rendered_content)
        self.assertIn(
            'Об используемых технологиях', response_tech.rendered_content
        )
