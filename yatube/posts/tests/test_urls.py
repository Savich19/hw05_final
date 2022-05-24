from http import HTTPStatus
from django.urls import reverse
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from posts.models import Group, Post, Comment
from django.core.cache import cache

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый текст',
            description='Тестовое описание',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            pub_date='Временное время',
            author=cls.user,
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            text='Тестовый комментарий',
            author=cls.user,
            post=cls.post,
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент автора
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # Создаем авторизованый клиент не автора
        self.user = User.objects.create_user(username='no auth')
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user)

    # Проверка вызываемых шаблонов для каждого адреса
    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/auth/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/unknown_page/': 'core/404.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_guest_pages_has_correct_http_status(self):
        """Тестируем доступность страниц неавторизованными пользователями."""
        urls = {
            reverse('posts:index'):
                HTTPStatus.OK,
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}):
                HTTPStatus.OK,
            reverse('posts:profile', kwargs={'username': 'auth'}):
                HTTPStatus.OK,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{self.post.id}'}
            ): HTTPStatus.OK,
        }
        for url, expected_value in urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, expected_value)

    def test_authorized_pages_has_correct_http_status(self):
        """Тестируем доступность страниц авторизованными пользователями."""
        urls = {
            reverse('posts:post_create'): HTTPStatus.OK,
        }
        for field, expected_value in urls.items():
            with self.subTest(field=field):
                response = self.authorized_client.get(field)
                self.assertEqual(response.status_code, expected_value)

    def test_author_pages_has_correct_http_status(self):
        """Тестируем доступность страниц автором."""
        urls = {
            reverse('posts:post_edit', kwargs={'post_id': f'{self.post.id}'}):
                HTTPStatus.OK,
        }
        for field, expected_value in urls.items():
            with self.subTest(field=field):
                response = self.authorized_client.get(field)
                self.assertEqual(response.status_code, expected_value)
                response = self.authorized_client_2.get(field)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    # Проверяем редиректы для неавторизованного пользователя
    def test_create_url_redirect_anonymous_on_admin_login(self):
        """Страница /create/ перенаправит анонимного пользователя
        на страницу логина."""
        response = self.client.get('/create/', follow=True)
        self.assertRedirects(
            response, ('/auth/login/?next=/create/'))

    def test_comment_url_redirect_authorized_on_post_detail(self):
        """Страница /comment/ перенаправит авторизированного пользователя
        на страницу комментируемого поста."""
        response = self.authorized_client.get(
            f'/posts/{self.post.id}/comment/',
            follow=True
        )
        self.assertRedirects(
            response,
            (f'/posts/{self.post.id}/')
        )
