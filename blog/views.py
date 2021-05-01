from django.shortcuts import render,redirect
from django.http import HttpResponse,HttpResponseRedirect
from django.contrib import messages
from.models import Blogpost, BlogCommet
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
import django.templatetags
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from urllib.parse import quote_plus
from django.http import JsonResponse
from django.core import serializers
# Create your views here.

def home(request):
    blogs = Blogpost.objects.all()
    params = {'blogs': blogs}
    return render(request,'blog/home.html',params)

def about(request):
    return render(request,'blog/about.html')

def blogpost(request,id):
    latests=Blogpost.objects.order_by('-pub_date')[:3]
    try:
        post = Blogpost.objects.get(post_id = id)
        share_string = quote_plus(post.title)
    except:
        messages.error(request,"Sommething Went wrong")
        return redirect("/")
    post.view= post.view+1
    post.save()
    comment = BlogCommet.objects.filter(post=post,parent=None)
    replies = BlogCommet.objects.filter(post=post).exclude(parent=None) 
    replyDict = {}
    for reply in replies:
        if reply.parent.comment_id not in replyDict.keys():
            replyDict[reply.parent.comment_id]=[reply]
        else:
            replyDict[reply.parent.comment_id].append(reply)
    return render(request, 'blog/blogpost.html',{'post':post,'comment':comment, 'user':request.user , 'replyDict':replyDict,'latests':latests,"share_string":share_string})


def search(request):
    query = request.GET.get('query')
    if len(query)==0:
        return redirect('/')
    if len(query)>80:
        blogs = []
    else:
        blogTitle = Blogpost.objects.filter(title__icontains=query)
        blogContant = Blogpost.objects.filter(contant__icontains=query)   
        blogs = blogTitle.union(blogContant)
    if blogs.count==0:
        messages.warning(request,"No search Found please refine your search ")
    return render(request,'blog/search.html',{'blogs':blogs, 'query': query})


def signup(request):
    if request.method == 'POST':
        username=request.POST['username']
        fname = request.POST['fname']
        lname = request.POST['lname']
        email=request.POST['email']
        password=request.POST['pass1']
        password2=request.POST['pass2']

        # checkpoints 
        #username length checker
        if len(username) > 12 :
            messages.error(request,'Your account not created Because')
            messages.error(request,'Username must have maximum 12 Charcters')
            messages.error(request,'Please fill SIGN UP form again')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

        # username charkters checker
        if not username.isalnum() :
             messages.error(request,'Your account not created Because')
             messages.error(request,'Username only contain alphaNumeric value')
             messages.error(request,'Please fill SIGN UP form again')
             return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))     

        # password1 and password2 checker     
        if password != password2 :
            messages.error(request,'Your account not created Because')
            messages.error(request,'Passwords do not match')
            messages.error(request,'Please fill SIGN UP form again')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        # creating user
        try:
            myuser=User.objects.get(username=username)
            messages.error(request,'The username you entered has already been taken. Please try another username.')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        except:
            myuser = User.objects.create_user(username=username,email=email,password=password)
            myuser.first_name= fname
            myuser.last_name= lname
            myuser.save()
            login(request,myuser)
            request.session['user'] == myuser
            messages.success(request,'Your account created succesfully')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        
    else:
        return HttpResponse('404 - Not Found')

def handlelogin(request):
    if request.method == "POST":
        username = request.POST["loginusername"]
        password = request.POST["loginpassword"]
        user = authenticate(username=username,password=password)
        if user is not None:
            login(request,user)
            request.session['user'] = user.username
            messages.success(request,"Successfully Logged in")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        else:
            messages.error(request,"Invalid Credentials, Please try again")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    else:
        return HttpResponse('Error Not Found 404')

def handlelogout(request):
    logout(request)
    request.session.flush()
    messages.success(request,"Successfully Logged Out")
    return redirect('/')

def postComment(request):
    if request.method == 'POST':
        comment = request.POST.get("comment")
        user = request.user
        postId = request.POST.get("post_id") 
        post = Blogpost.objects.get(post_id=postId)
        parentId = request.POST.get("reply_id")        
        if parentId == "": 
            if len(comment) > 0:
                comment = BlogCommet(comment=comment,user=user,post=post)
                comment.save()
                messages.success(request,"Comment posted successfully")
            else:
                messages.warning(request,"Comment block never blank Please write something")  
        else:
            parent = BlogCommet.objects.get(comment_id=parentId)
            comment = BlogCommet(comment=comment,user=user,post=post,parent=parent)
            comment.save()
            messages.success(request,"Reply posted successfully")      
    return redirect(f"/blogpost/{post.post_id}")



def trending(request):
    blogs = Blogpost.objects.order_by('-pub_date','view')[:10]
    params = {'blogs': blogs}
    return render(request,'blog/trending.html',params)



def post_blog(request):
    try:
        user = request.session['user']
        print("user==",user)
    except:
        messages.warning(request,"Please Login")
        return redirect("/")
    if user:
        if request.is_ajax and request.method=="POST":
            title = request.POST.get("title")
            img_url = request.POST.get("img_url")
            contant = request.POST.get("contant")
            user = request.user
            post = Blogpost(user=user,title=title,IMG_url=img_url,contant=contant)
            post.save()
            messages.success(request,"Post Created Successfully")
            return redirect("blogpost",post.post_id)
        return render(request,"blog/post_blog.html")
    messages.error(request,"Login For create New Blog")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    
def user_posts(request):
    try:
        user = request.session['user']
        print("user==",user)
    except:
        messages.warning(request,"Please Login")
        return redirect("/")
    if user:
        user = request.user
        posts = Blogpost.objects.filter(user=user)
        return render(request,"blog/user_posts.html",{"blogs":posts})
    return HttpResponse("Something Went Wrong")


def delete_post(request,id):
    try:
        user = request.session['user']
        print("user==",user)
    except:
        messages.warning(request,"Please Login")
        return redirect("/")
    if user:
        try:
            post = Blogpost.objects.get(post_id=id)
            if request.user==post.user:
                post.delete()
                messages.success(request,"Post Deleted Successfully")
            else:
                messages.error(request,"You are not Authenticated for this action")
            return redirect("/")
        except:
            messages.error(request,"Post not available")
            return redirect("/")
    