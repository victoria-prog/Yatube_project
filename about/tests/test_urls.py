from http import HTTPStatus

from django.test import TestCase


class AboutURLTests(TestCase):
    # Проверяем доступность страниц для любого пользователя
    def test_urls_exists_at_desired_location(self):
        """Страницы '/about/author/', '/about/tech/'
        доступны любому пользователю."""
        url_adresses = {
            '/about/author/': HTTPStatus.OK.value,
            '/about/tech/': HTTPStatus.OK.value
        }
        for adress, status_code in url_adresses.items():
            with self.subTest():
                response = self.client.get(adress)
                self.assertEqual(response.status_code, status_code)
