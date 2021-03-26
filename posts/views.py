from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render, reverse

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post

User = get_user_model()


def index(request):
    is_index = True
    post_list = Post.objects.select_related('author').all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'posts/index.html', {
        'paginator': paginator, 'page': page,
        'post_list': post_list, 'is_index': is_index
    })


def group_posts(request, slug):
    is_group = True
    group = get_object_or_404(Group, slug=slug)
    group_posts = group.posts.select_related('author').all()
    paginator = Paginator(group_posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'posts/group.html', {
        'group': group, 'page': page,
        'group_posts': group_posts,
        'paginator': paginator, 'is_group': is_group
    })


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('index')
    return render(request, 'posts/new_post.html', {'form': form})


def profile(request, username):
    is_following = False
    is_profile = True
    user = get_object_or_404(User, username=username)
    post_list = Post.objects.filter(author=user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    if request.user.is_authenticated:
        is_following = Follow.objects.filter(
            user=request.user, author=user
        ).exists()
    return render(request, 'posts/profile.html', {
        'post_list': post_list,
        'page': page, 'author': user,
        'is_profile': is_profile,
        'following': is_following
    })


def post_view(request, username, post_id):
    is_post = True
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post=post)
    return render(request, 'posts/post.html', {
        'post': post, 'author': post.author, 'comments': comments,
        'form': form, 'is_post': is_post
    })


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    if post.author != request.user:
        return redirect(reverse('post', args=[username, post_id]))
    form = PostForm(
        data=request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect(reverse('post', args=[username, post_id]))
    return render(request, 'posts/new_post.html', {'form': form, 'post': post})


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect(reverse('post', args=[username, post_id]))
    return render(
        request, 'includes/comments.html', {'form': form, 'post': post}
    )


@login_required
def follow_index(request):
    favor_posts = Post.objects.filter(
        author__following__user=request.user
    )
    paginator = Paginator(favor_posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'posts/follow.html', {
        'favor_posts': favor_posts,
        'paginator': paginator,
        'page': page
    })


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect(reverse('profile', args=[username]))


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    following = get_object_or_404(Follow, user=request.user, author=author)
    following.delete()
    return redirect(reverse('profile', args=[username]))


def page_not_found(request, exception):
    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=404
    )


def server_error(request):
    return render(request, 'misc/500.html', status=500)
