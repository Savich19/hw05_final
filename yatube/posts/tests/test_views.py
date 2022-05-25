import shutil
import tempfile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms

from posts.models import Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый текст',
            description='Тестовое описание',
            slug='test-slug',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовый текст_2',
            description='Тестовое описание_2',
            slug='test-slug-2',
        )
        cls.group_3_img = Group.objects.create(
            title='Тестовый текст_3',
            description='Тестовое описание_3 для поста с картинкой',
            slug='test-slug-3',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст для поста с группой',
            author=cls.user,
            group=cls.group,

        )
        cls.post_2 = Post.objects.create(
            text='Тестовый текст для поста без группы',
            author=cls.user,
        )
        cls.post_3_img = Post.objects.create(
            text='Тестовый текст для поста с группой и картинкой',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаём неавторизованный клиент
        self.guest_client = Client()
        # Создаём авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        # Собираем в словарь пары "reverse(name): имя_html_шаблона"
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.post.author.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        # Проверяем, что при обращении к name
        # вызывается соответствующий HTML-шаблон
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    # Задание 2. Проверяем контекст на соответвие ожиданиям
    def check_context_page_obj(self, response):
        """Пост соответствует ожиданиям"""
        response_post = response.context.get('page_obj')[0]
        post_text = response_post.text
        post_author = response_post.author
        post_group = response_post.group
        post_image = response_post.image
        self.assertEqual(post_text, self.post_3_img.text)
        self.assertEqual(post_author, self.post_3_img.author)
        self.assertEqual(post_group, self.post_3_img.group)
        self.assertEqual(post_image, self.post_3_img.image)

    def check_form(self, response):
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        # Типы полей формы в словаре context соответствуют ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    # 01.1 проверяем контекст index
    def test_index_page_show_correct_context(self):
        """Словарь шаблона index сформирован с правильным контекстом."""
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        self.check_context_page_obj(response)

    # 02.1 проверяем контекст group_list
    def test_group_list_page_show_correct_context(self):
        """Словарь шаблона group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            )
        )
        self.check_context_page_obj(response)
        self.assertEqual(response.context.get('group'), self.group)
        self.assertEqual(
            response.context.get('title'),
            'Записи сообщества'
        )

    # 03.1 проверяем контекст profile
    def test_profile_page_show_correct_context(self):
        """Словарь шаблона profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.post.author.username}
            )
        )
        self.check_context_page_obj(response)
        self.assertEqual(response.context.get('author'), self.post.author)

    # 04.1 проверяем контекст post_detail
    def test_post_detail_page_show_correct_context(self):
        """Словарь шаблона post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            )
        )
        self.assertEqual(response.context.get('post_number'), self.post)

    # 05.1 проверяем контекст post_edit
    def test_post_edit_page_show_correct_context(self):
        """Словарь шаблона post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            )
        )
        self.check_form(response)
        self.assertEqual(response.context.get('is_edit'), True)
        self.assertEqual(
            response.context.get('title'),
            'Редактировать пост'
        )
        form_text = response.context.get('form')['text'].value()
        form_group = response.context.get('form')['group'].value()
        self.assertEqual(form_text, self.post.text)
        self.assertEqual(form_group, self.post.group.id)

    # 06.1 проверяем контекст post_create
    def test_post_create_page_show_correct_context(self):
        """Словарь шаблона post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.check_form(response)
        self.assertEqual(response.context.get('is_edit'), False)
        self.assertEqual(
            response.context.get('title'),
            'Новый пост'
        )

    # Задание 3
    def test_grouped_post_show_in_pages(self):
        """Проверяем что пост с группой попадает на страницы."""
        cache.clear()
        group_post_pages = {
            reverse('posts:index'): 3,
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}): 2,
            reverse('posts:profile', kwargs={'username': 'auth'}): 3,
        }
        for value, expected in group_post_pages.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                self.assertEqual(len(response.context["page_obj"]), expected)

    def test_new_group_page_dont_have_a_post(self):
        """Проверяем что страница новой группы не имеет постов."""
        url = reverse('posts:group_list', args=['test-slug-2'])
        response = self.authorized_client.get(url)
        self.assertEqual(len(response.context["page_obj"]), 0)

    # Спринт 6: проверка кэша
    def test_cache_in_index_page_show_correct_context(self):
        """Проверка работы кэша на главной странице."""
        Post.objects.create(
            text='Тестовый текст для удаляемого поста',
            author=self.user,
        )
        len_posts = Post.objects.count()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context.get('page_obj')), len_posts)
        Post.objects.last().delete()
        self.assertEqual(len(response.context.get('page_obj')), len_posts)
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context.get('page_obj')), len_posts - 1)


class PaginatorViewsTest(TestCase):
    """Класс с тестами пагинатора"""
    # Здесь создаются фикстуры: клиент и 13 тестовых записей.
    POSTS_ALL = 13
    POSTS_PAGE = 10

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый текст',
            description='Тестовое описание',
            slug='test-slug',
        )
        Post.objects.bulk_create([
            Post(
                text=f'Пост № {i}',
                author=cls.user,
                group=cls.group,
            )
            for i in range(cls.POSTS_ALL)
        ])

    def setUp(self):
        # Создаём авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)

    def test_first_page_contains_records(self):
        """Тестируем первую страницу пагинатора"""
        cache.clear()
        paginator_pages = {
            reverse('posts:index'): 'page_obj',
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}
            ): 'page_obj',
            reverse(
                'posts:profile',
                kwargs={'username': 'auth'}
            ): 'page_obj',
        }
        for reverse_name, obj in paginator_pages.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(len(response.context[obj]), self.POSTS_PAGE)

    def test_second_page_contains_records(self):
        """Тестируем вторую страницу пагинатора"""
        cache.clear()
        paginator_pages = {
            reverse('posts:index'): 'page_obj',
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}
            ): 'page_obj',
            reverse(
                'posts:profile',
                kwargs={'username': 'auth'}
            ): 'page_obj',
        }
        for reverse_name, obj in paginator_pages.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name + '?page=2')
                self.assertEqual(
                    len(response.context[obj]),
                    self.POSTS_ALL % self.POSTS_PAGE
                )
