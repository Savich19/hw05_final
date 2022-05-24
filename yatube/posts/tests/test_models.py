from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Comment, Group, Post

User = get_user_model()
LEN_POST_TEXT = 15


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
        )
        cls.comment = Comment.objects.create(
            text='Тестовый комментарий',
            author=cls.user,
            post=cls.post,
        )

    def test_models_post_have_correct_object_names(self):
        """Проверяем, что у модели Post корректно работает __str__."""
        post = PostModelTest.post
        expected_object_name = post.text[:LEN_POST_TEXT]
        self.assertEqual(expected_object_name, str(post))

    def test_models_group_have_correct_object_names(self):
        """Проверяем, что у модели Group корректно работает __str__."""
        group = PostModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))

    def test_models_comment_have_correct_object_names(self):
        """Проверяем, что у модели Comment корректно работает __str__."""
        comment = PostModelTest.comment
        expected_object_name = comment.text[:LEN_POST_TEXT]
        self.assertEqual(expected_object_name, str(comment))
