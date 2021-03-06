import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post, Profile

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='TestName')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.author,
            group=cls.group,
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.DIR_UPLOAD_TO = cls.post._meta.get_field('image').upload_to

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.author)
        self.not_author = User.objects.create_user(username='NotAuthor')
        self.not_author_client = Client()
        self.not_author_client.force_login(self.not_author)

    def test_post_create(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        text_for_post = 'Тестовый пост 2'
        self.assertFalse(
            Post.objects.filter(
                text=text_for_post,
                author=self.author,
                group=self.group.id,
                image=f'{self.DIR_UPLOAD_TO}{self.uploaded}',
            ).exists()
        )
        form_data = {
            'text': text_for_post,
            'group': self.group.id,
            'image': self.uploaded,
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response, reverse('posts:profile', args=(self.author,))
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=text_for_post,
                author=self.author,
                group=self.group.id,
                image=f'{self.DIR_UPLOAD_TO}{self.uploaded}',
            ).exists()
        )

    def test_post_edit(self):
        """Валидная форма редактирует запись в Post."""
        posts_count = Post.objects.count()
        text_for_post_edit = 'Тестовый пост с изменениями'
        self.assertFalse(
            Post.objects.filter(
                text=text_for_post_edit,
                author=self.author,
                group=self.group.id,
            ).exists()
        )
        form_data = {
            'text': text_for_post_edit,
            'group': self.group.id,
        }
        response = self.author_client.post(
            reverse('posts:post_edit', args=(self.post.id,)),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response, reverse('posts:post_detail', args=(self.post.id,))
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                id=self.post.id,
                text=text_for_post_edit,
                author=self.author,
                group=self.group.id,
            ).exists()
        )

    def test_comment_create(self):
        """Валидная форма создает запись в Comment."""
        comments_count = Comment.objects.count()
        text_for_comment = 'Тестовый коммент'
        self.assertFalse(
            Comment.objects.filter(
                text=text_for_comment,
                author=self.not_author,
                post=self.post.id,
            ).exists()
        )
        form_data = {
            'text': text_for_comment,
        }
        response = self.not_author_client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response, reverse('posts:post_detail', args=(self.post.id,))
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text=text_for_comment,
                author=self.not_author,
                post=self.post.id,
            ).exists()
        )
        last_comment = Comment.objects.latest('id')
        self.assertEqual(last_comment.post.id, self.post.id)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ProfileFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.DIR_UPLOAD_TO = Profile._meta.get_field('avatar').upload_to

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(username='TestName')
        self.user_client = Client()
        self.user_client.force_login(self.user)

    def test_profile_with_avatar_create(self):
        """Валидная форма создает запись в Profile."""
        profile_count = Profile.objects.count()
        self.assertFalse(
            Profile.objects.filter(
                user=self.user,
                avatar=f'{self.DIR_UPLOAD_TO}{self.uploaded}',
            ).exists()
        )
        form_data = {
            'user': self.user,
            'avatar': self.uploaded,
        }
        response = self.user_client.post(
            reverse('posts:avatar', args=(self.user,)),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response, reverse('posts:profile', args=(self.user,))
        )
        self.assertEqual(Profile.objects.count(), profile_count + 1)
        self.assertTrue(
            Profile.objects.filter(
                user=self.user,
                avatar=f'{self.DIR_UPLOAD_TO}{self.uploaded}',
            ).exists()
        )
