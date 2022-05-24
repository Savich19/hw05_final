# from functools import cache
from enum import auto
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from .models import Comment, Follow, Group, Post, User
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page


CNT_POSTS = 10


def create_pages(request, posts, cnt):
    paginator = Paginator(posts, cnt)
    # Из URL извлекаем номер запрошенной страницы - это значение page
    page_number = request.GET.get('page')
    # Получаем набор записей для страницы с запрошенным номером
    page_obj = paginator.get_page(page_number)
    return page_obj


@cache_page(20, key_prefix='index_page')
def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.select_related()
    page_obj = create_pages(request, post_list, CNT_POSTS)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    title = 'Записи сообщества'
    group = get_object_or_404(Group, slug=slug)
    # post_list = Post.objects.filter(group=group).order_by('-pub_date')
    post_list = group.posts.select_related()
    page_obj = create_pages(request, post_list, CNT_POSTS)
    context = {
        'group': group,
        'page_obj': page_obj,
        'title': title,
    }
    return render(request, template, context)


def profile(request, username):
    # Здесь код запроса к модели и создание словаря контекста
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related()
    page_obj = create_pages(request, post_list, CNT_POSTS)
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            author__following__user=request.user, author=author).exists()
    context = {
        'page_obj': page_obj,
        'author': author,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    # Здесь код запроса к модели и создание словаря контекста
    template = 'posts/post_detail.html'
    post_number = get_object_or_404(Post, pk=post_id)
    form = CommentForm()
    comments = post_number.comments.select_related()
    context = {
        'post_number': post_number,
        'form': form,
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    title = 'Новый пост'
    is_edit = False
    form = PostForm(
        data=request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect('posts:profile', request.user)
    context = {
        'form': form,
        'is_edit': is_edit,
        'title': title,
    }
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    title = 'Редактировать пост'
    is_edit = True
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        data=request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        # 'post': post,
        'form': form,
        'is_edit': is_edit,
        'title': title,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    # Получите пост
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    # информация о текущем пользователе доступна в переменной request.user
    # ...
    template = 'posts/follow.html'
    #post_list = Post.objects.select_related()
    post_list=Post.objects.filter(author__following__user=request.user)
    page_obj = create_pages(request, post_list, CNT_POSTS)

    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    """View функция для подписки на автора."""
    follow_author = get_object_or_404(User, username=username)
    follow_user = get_object_or_404(User, username=request.user)
    if follow_user != follow_author:
        Follow.objects.get_or_create(
            author=follow_author,
            user=follow_user,
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    """View функция для отписки от автора."""
    follow_author = get_object_or_404(User, username=username)
    follow_user = get_object_or_404(User, username=request.user)
    follow_profile = Follow.objects.get(author=follow_author,
                                        user=follow_user)
    if Follow.objects.filter(id=follow_profile.id).exists():
        follow_profile.delete()
    return redirect('posts:profile', username=username)
'''NEW


@login_required
def profile_follow(request, username):
    """View функция для подписки на автора."""
    follow_author = get_object_or_404(User, username=username)
    follow_user = get_object_or_404(User, username=request.user)
    # if follow_user != follow_author:
    Follow.objects.get_or_create(
        author=follow_author,
        user=follow_user,
    )
    return redirect('posts:follow_index')
'''