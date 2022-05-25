from django.test import Client, TestCase
from posts.models import Follow, Group, Post
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_2 = User.objects.create_user(username='auth_2')
        cls.user_3 = User.objects.create_user(username='auth_3')
        cls.group = Group.objects.create(
            title='Тестовый текст',
            description='Тестовое описание',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост автора № 1',
            author=cls.user,
            group=cls.group,
        )
        cls.post = Post.objects.create(
            text='Тестовый пост автора № 2',
            author=cls.user_2,
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_authorized_client_follow(self):
        """Авторизованный пользователь имеет возможность
        подписываться на и отписываться от других авторов."""
        # проверка подписки
        follow_cnt_1 = Follow.objects.count()
        response = self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user_2.username}
        ))
        follow_cnt_2 = Follow.objects.count()
        self.assertRedirects(
            response, f'/profile/{self.user_2.username}/'
        )
        self.assertEqual(follow_cnt_2 - follow_cnt_1, 1)
        # проверка отписки
        response = self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.user_2.username}
        ))
        follow_cnt_3 = Follow.objects.count()
        self.assertRedirects(
            response, f'/profile/{self.user_2.username}/'
        )
        self.assertEqual(follow_cnt_3, follow_cnt_1)

    def test_post_in_follow(self):
        """Новая запись пользователя появляется в ленте тех, кто на него
        подписан и не появляется в ленте тех, кто не подписан."""
        response = self.authorized_client.get(reverse('posts:follow_index'))
        post_cnt_1 = len(response.context.get('page_obj'))
        Follow.objects.get_or_create(user=self.user, author=self.user_2)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        post_cnt_2 = len(response.context.get('page_obj'))
        self.assertEqual(post_cnt_2 - post_cnt_1, 1)

        self.authorized_client.force_login(self.user_3)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        post_cnt_3 = len(response.context.get('page_obj'))
        self.assertEqual(post_cnt_3, 0)
