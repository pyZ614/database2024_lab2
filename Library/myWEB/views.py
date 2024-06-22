from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.contrib.auth.hashers import make_password, check_password  # 用户密码管理
from django.utils import timezone  # django带时区管理的时间类
from .models import Reader_Table, Admin_Table, Bname_Table, Book_Table, Borrow_Table, Reserve_Table  # 引入数据库、
from datetime import timedelta
from django.conf import settings
from django.db import connection

def home(request):
    return render(request, 'home.html')


def login_view(request):  # 读者、管理员用户登录
    context = dict()    # 创建一个空字典 context，用于传递数据。
    if request.method == 'POST':
        context["username"] = username = request.POST.get("username")
        password = request.POST.get("password")
        if not username:
            context["msg"] = "请输入读者id或图书管理员工号"
            return render(request, 'home.html', context=context)
        if not password:
            context["msg"] = "密码不能为空"
            return render(request, 'home.html', context=context)
        elif 'gh' in username:  # 管理员使用工号登录
            result = Admin_Table.objects.filter(aid=username)
            if result.exists() and password == result[0].psw:  # 管理员登录成功,设置 session 数据表示管理员已登录
                request.session['login_type'] = 'admin'
                request.session['id'] = result[0].aid
                request.session['aname'] = result[0].aname
                return redirect('/admin_index/')
            else:
                context["msg"] = "账号或密码输入错误"
                return render(request, 'home.html', context=context)
        else:  # 读者使用id登录
            username = username.lstrip('0')
            result = Reader_Table.objects.filter(rid=username)
            if result.exists() and password == result[0].psw:  # 读者id登录成功
                request.session['login_type'] = 'reader'
                request.session['id'] = result[0].rid
                request.session['rname'] = result[0].rname
                return redirect('/reader_index/')
            else:
                context["msg"] = "账号或密码输入错误"
                return render(request, 'home.html', context=context)
    else:
        return render(request, 'home.html')


def logout_view(request):  # 读者、管理员退出登录
    if request.session.get('login_type', None):
        request.session.flush()  # 清空会话
    return HttpResponseRedirect("/")


"""
登录后的session:
request.session['login_type']: 读者'reader'  管理员'admin'
request.session['r/aid']: 读者id  管理员工号 
request.session['r/aname']: 读者姓名 管理员姓名
"""

# =====================读者======================


def reader_index(request):  # 读者首页
    if request.session.get('login_type', None) != 'reader':
        return HttpResponseRedirect("/")
    context = dict()
    context['rname'] = request.session.get('rname')
    return render(request, 'reader_index.html', context=context)


def reader_search(request):  # 读者书目状态查询
    if request.session.get('login_type', None) != 'reader':
        return HttpResponseRedirect("/")
    context = dict()
    context['rname'] = request.session.get('rname', None)
    if request.method == 'GET':
        return render(request, 'reader_search.html', context=context)
    else:  # POST
        context['bname'] = bname = request.POST.get('bname')  # 书名
        context['author'] = author = request.POST.get('author')  # 作者
        context['isbn'] = isbn = request.POST.get('isbn')  # ISBN
        context['pub'] = pub = request.POST.get('pub')  # 出版社
        context['msg'] = "未知错误，请重试"
        result = Bname_Table.objects.all()
        if not bname and not author and not isbn and not pub:
            context['msg'] = "请输入有效筛选信息！"
            return render(request, 'reader_search.html', context=context)
        if bname: #根据用户输入的书名、作者、ISBN 和出版社对 result 进行过滤
            result = result.filter(bname__contains=bname)
        if author:
            result = result.filter(author__contains=author)
        if isbn:
            result = result.filter(isbn__startswith=isbn)
        if pub:
            result = result.filter(pub__contains=pub)
        book_status = []
        for elem in result:
            book_status.append(
                {
                    'ISBN': elem.isbn,
                    'bname': elem.bname,
                    'author': elem.author,
                    'pub': elem.pub,
                    'pubtime': elem.pubtime,
                    'own': len(Book_Table.objects.filter(isbn=elem.isbn)),
                    'not_yet_borrow': len(Book_Table.objects.filter(isbn=elem.isbn, status='未借出')),
                    'borrowed': len(Book_Table.objects.filter(isbn=elem.isbn, status='已借出')),
                    'reserved': len(Book_Table.objects.filter(isbn=elem.isbn, status='已预约')),
                }
            )
        context['msg'] = ''
        context['book_status'] = book_status
        return render(request, 'reader_search.html', context=context)



def reader_reserve(request):  # 读者预约登记
    if request.session.get('login_type', None) != 'reader':
        return HttpResponseRedirect("/")
    context = dict()
    context['rname'] = request.session.get('rname', None)
    reserve_reg = []
    result = Reserve_Table.objects.filter(rid_id=request.session.get('id', None))
    for elem in result:
        reserve_reg.append(
            {
                'ISBN': elem.isbn.isbn,
                'bname': Bname_Table.objects.get(isbn=elem.isbn.isbn).bname,
                'reserve_time': elem.reserve_time,
                'bid': elem.bid.bid if elem.bid else None,
            }
        )
    context['reserve_reg'] = reserve_reg
    if request.method == 'GET':
        return render(request, 'reader_reserve.html', context=context)
    elif request.method == 'POST':
        context['msg'] = "未知错误，请重试"
        context['ISBN'] = isbn = request.POST.get('ISBN')
        if not isbn:
            context['msg'] = "请填写ISBN号进行预约登记"
            return render(request, 'reader_reserve.html', context=context)
        result = Bname_Table.objects.filter(isbn=isbn)
        if not result.exists():
            context['msg'] = "ISBN输入有误或馆藏没有此图书请重试"
            return render(request, 'reader_reserve.html', context=context)
        result = Reserve_Table.objects.filter(isbn=isbn, rid=request.session.get('id', None))
        if result.exists():
            context['msg'] = "您已预约该书，请勿重复预约！"
            return render(request, 'reader_reserve.html', context=context)
        id = Book_Table.objects.filter(isbn=isbn,status = '未借出')
        if id.exists():
            item = Reserve_Table(
                rid_id=request.session.get('id', None),
                isbn=Bname_Table.objects.get(isbn=isbn),
                reserve_time=timezone.now(),
                bid_id = id[0].bid,
            )
            item.save()
            # 更新对应的图书状态为已预约
            book = Book_Table.objects.get(bid=id[0].bid)
            book.status = '已预约'  
            book.save()
            result = Reserve_Table.objects.filter(rid_id=request.session.get('id', None))
            for elem in result:
                reserve_reg.append(
                {
                    'ISBN': elem.isbn.isbn,
                    'bname': Bname_Table.objects.get(isbn=elem.isbn.isbn).bname,
                    'reserve_time': elem.reserve_time,
                    'bid': elem.bid.bid if elem.bid else None,
                    }
                )
            context['reserve_reg'] = reserve_reg
            context['msg'] = "预约成功"
        return render(request, 'reader_reserve.html', context=context)
    
def reader_reserve2(request):  # 读者取消预约
    if request.session.get('login_type', None) != 'reader':
        return HttpResponseRedirect("/")
    
    context = dict()
    context['rname'] = request.session.get('rname', None)
    reserve_reg = []
    
    # 获取当前读者的预约记录
    result = Reserve_Table.objects.filter(rid_id=request.session.get('id', None))
    for elem in result:
        reserve_reg.append(
            {
                'ISBN': elem.isbn.isbn,
                'bname': Bname_Table.objects.get(isbn=elem.isbn.isbn).bname,
                'reserve_time': elem.reserve_time,
                'bid': elem.bid.bid if elem.bid else None,
            }
        )
    context['reserve_reg'] = reserve_reg
    
    if request.method == 'GET':
        return render(request, 'reader_reserve2.html', context=context)
    
    elif request.method == 'POST':
        context['msg'] = "未知错误，请重试"
        context['ISBN'] = isbn = request.POST.get('ISBN')
        if not isbn:
            context['msg'] = "请填写ISBN号进行取消预约"
            return render(request, 'reader_reserve2.html', context=context)
        
        result = Reserve_Table.objects.filter(isbn=isbn, rid=request.session.get('id', None))
        if not result.exists():
            context['msg'] = "您未预约该书，请检查ISBN号是否正确"
            return render(request, 'reader_reserve2.html', context=context)
        
        # 删除预约记录
        result.delete()
        context['msg'] = "预约已成功取消"

        
        # 更新预约记录
        reserve_reg = []
        result = Reserve_Table.objects.filter(rid_id=request.session.get('id', None))
        for elem in result:
            reserve_reg.append(
                {
                    'ISBN': elem.isbn.isbn,
                    'bname': Bname_Table.objects.get(isbn=elem.isbn.isbn).bname,
                    'reserve_time': elem.reserve_time,
                    'bid': elem.bid.bid if elem.bid else None,
                }
            )
        context['reserve_reg'] = reserve_reg
        
        return render(request, 'reader_reserve2.html', context=context)

    
def reader_person(request):  # 读者个人(借书)状态查询
    if request.session.get('login_type', None) != 'reader':
        return HttpResponseRedirect("/")
    context = dict()
    context['rname'] = request.session.get('rname', None)
    result = Borrow_Table.objects.filter(rid_id=request.session.get('id'))
    reader0 = []
    for elem in result:
        reader0.append(
            {
                'bid': elem.bid.bid,
                'bname': elem.bid.isbn.bname,
                'borrow_time': elem.borrow_time,
                'return_date': elem.return_date,
                'return_time': elem.return_time
            }
        )
    context['reader0'] = reader0
    return render(request, 'reader_person.html', context=context)


# =====================管理员======================


def admin_index(request):  # 管理员首页
    if request.session.get('login_type', None) != 'admin':
        return HttpResponseRedirect("/")
    context = dict()
    context['aname'] = request.session.get('aname')
    return render(request, 'admin_index.html', context=context)


def admin_search(request):  # 管理员书目状态查询
    if request.session.get('login_type', None) != 'admin':
        return HttpResponseRedirect("/")
    context = dict()
    context['aname'] = request.session.get('aname', None)
    if request.method == 'GET':
        return render(request, 'admin_search.html', context=context)
    else:
        context['bname'] = bname = request.POST.get('bname')  # 书名
        context['author'] = author = request.POST.get('author')  # 作者
        context['isbn'] = isbn = request.POST.get('isbn')  # ISBN
        context['pub'] = pub = request.POST.get('pub')  # 出版社
        context['msg'] = "未知错误，请重试"
        result = Bname_Table.objects.all()
        if bname:
            result = result.filter(bname__contains=bname)
        if author:
            result = result.filter(author__contains=author)
        if isbn:
            result = result.filter(isbn__startswith=isbn)
        if pub:
            result = result.filter(pub__contains=pub)
        book_status = []
        for elem in result:
            if len(Book_Table.objects.filter(isbn=elem.isbn))!=0:
                book_status.append(
                    {
                        'ISBN': elem.isbn,
                        'bname': elem.bname,
                        'author': elem.author,
                        'pub': elem.pub,
                        'pubtime': elem.pubtime,
                        'own': len(Book_Table.objects.filter(isbn=elem.isbn)),
                        'not_yet_borrow': len(Book_Table.objects.filter(isbn=elem.isbn, status='未借出')),
                        'borrowed': len(Book_Table.objects.filter(isbn=elem.isbn, status='已借出')),
                        'reserved': len(Book_Table.objects.filter(isbn=elem.isbn, status='已预约')),
                        'book_image': elem.book_image
                    }
                )
        context['msg'] = ''
        context['book_status'] = book_status
        return render(request, 'admin_search.html', context=context)





def admin_in(request): # 管理员入库图书
    if request.session.get('login_type', None) != 'admin':
        return HttpResponseRedirect("/")
    
    context = {
        'aname': request.session.get('aname')
    }
    
    if request.method == 'GET':
        return render(request, 'admin_in.html', context=context)
    
    elif request.method == 'POST':
        isbn = request.POST.get('isbn')
        num = request.POST.get('num')
        bname = request.POST.get('bname')
        author = request.POST.get('author')
        pub = request.POST.get('pub')
        pubtime = request.POST.get('pubtime')
        book_image = request.FILES.get('book_image')  # 获取上传的图书封面图片
        if not (isbn and num):
            context['msg'] = "请填写ISBN号、入库数量"
            return render(request, 'admin_in.html', context=context)
        
        admin_id = request.session.get('id') # 获取管理员的 ID 并创建一个数据库游标对象，用于执行存储过程
        cursor = connection.cursor() 
        try:
            cursor.callproc('manage_book_stock', [
                isbn, int(num), bname, author, pub, pubtime, admin_id, ''
            ])
            cursor.execute('SELECT @_manage_book_stock_7') #调用存储过程
            message = cursor.fetchone()[0]
            context['msg'] = message
            
            # 如果有上传的图书封面图片，则保存到数据库
            if book_image:
                bname_obj = Bname_Table.objects.get(isbn=isbn)
                bname_obj.book_image = book_image
                bname_obj.save()
                context['msg'] += " 图书封面上传成功！"
            
        finally:
            cursor.close()
        
        return render(request, 'admin_in.html', context=context)




def admin_out(request):  # 管理员出库
    if request.session.get('login_type', None) != 'admin':
        return HttpResponseRedirect("/")
    context = dict()
    context['aname'] = request.session.get('aname')
    if request.method == 'GET':
        return render(request, 'admin_out.html', context=context)
    else:
        context['isbn'] = isbn = request.POST.get('isbn')  # ISBN
        context['num'] = num = request.POST.get('num')  # 出库数量
        context['msg'] = "未知错误，请重试"
        if not isbn or not num :
            context['msg'] = "请填写ISBN号、入出库数量"
            return render(request, 'admin_out.html', context=context)
        result = Bname_Table.objects.filter(isbn=isbn)
        if not result.exists():
            context['msg'] = "ISBN录入有误，请检查"
            return render(request, 'admin_out.html', context=context)
        not_yet_borrowed = Book_Table.objects.filter(isbn_id=isbn, status='未借出')  # 未借出图书数量
        reserved = Book_Table.objects.filter(isbn_id=isbn, status='已预约')  # 已预约图书数量
        borrowed = Book_Table.objects.filter(isbn_id=isbn, status='已借出')
        book = Book_Table.objects.filter(isbn_id=isbn)  # 所有图书数量
        num = int(num)
        if len(book) < num:
            context['msg'] = "出库数量不足！请检查"
            return render(request, 'admin_out.html', context=context)
        out = []
        for elem in not_yet_borrowed:
            if num > 0:
                out.append(elem)
                num -= 1
            else:
                break
        for elem in out:
            elem.delete()
        context['msg'] = "出库成功！"

        return render(request, 'admin_out.html', context=context)
    

def admin_borrow(request):  # 管理员借书
    if request.session.get('login_type', None) != 'admin':
        return HttpResponseRedirect("/")
    context = dict()
    context['aname'] = request.session.get('aname')
    if request.method == 'GET':
        return render(request, 'admin_borrow.html', context=context)
    else:
        context['rid'] = rid = request.POST.get('rid')
        context['isbn'] = isbn = request.POST.get('isbn')
        context['msg'] = "未知错误，请重试"
        if not rid or not isbn:
            context['msg'] = "请填写完整的读者id和ISBN号"
            return render(request, 'admin_borrow.html', context=context)
        if not rid.isdecimal():
            context['msg'] = "读者id不存在！"
            return render(request, 'admin_borrow.html', context=context)
        result = Reader_Table.objects.filter(rid=rid)
        if not result.exists():
            context['msg'] = "读者id不存在！"
            return render(request, 'admin_borrow.html', context=context)
        result = Bname_Table.objects.filter(isbn=isbn)
        if not result.exists():
            context['msg'] = "ISBN号填写错误，不存在该类书籍！"
            return render(request, 'admin_borrow.html', context=context)
        result = Borrow_Table.objects.filter(rid_id=rid, return_time=None)
        if len(result) >= 10:
            context['msg'] = "该读者借阅书籍数已经达到上限！"
            return render(request, 'admin_borrow.html', context=context)
        result = Reserve_Table.objects.filter(rid_id=rid, isbn_id=isbn)
        if result.exists() and result[0].bid_id is not None:  # 借书有过预约，且预约成功（删除预约、添加借书信息、修改图书状态）
            item = Borrow_Table(
                rid_id=rid,
                bid=result[0].bid,
                borrow_time=timezone.now(),
                return_date=timezone.now() + timezone.timedelta(days=60)
            )
            result[0].delete()  # 删除预约
            item.save()  # 添加借书信息
            context['msg'] = "借阅成功！（图书id：" + str(item.bid.bid) + "）"
            return render(request, 'admin_borrow.html', context=context)
        else:  # 未预约无法借书（添加借书信息、修改图书状态）
            context['msg'] = "未预约，无法借阅！"
            return render(request, 'admin_borrow.html', context=context)


def admin_return(request):  # 管理员还书
    if request.session.get('login_type', None) != 'admin':
        return HttpResponseRedirect("/")
    context = dict()
    context['aname'] = request.session.get('rname')
    if request.method == 'GET':
        return render(request, 'admin_return.html', context=context)
    else:
        context['rid'] = rid = request.POST.get('rid')
        context['bid'] = bid = request.POST.get('bid')
        context['msg'] = "未知错误，请重试"
        if not rid or not bid:
            context['msg'] = "请填写完整的读者id和ISBN号"
            return render(request, 'admin_return.html', context=context)
        if not rid.isdecimal() or not bid.isdecimal():
            context['msg'] = "读者id和图书id必须是数字！"
            return render(request, 'admin_return.html', context=context)
        result = Reader_Table.objects.filter(rid=rid)
        if not result.exists():
            context['msg'] = "读者id不存在！"
            return render(request, 'admin_return.html', context=context)
        result = Book_Table.objects.filter(bid=bid)
        if not result.exists():
            context['msg'] = "不存在该图书id！"
            return render(request, 'admin_return.html', context=context)
        result = Borrow_Table.objects.filter(rid_id=rid, bid_id=bid, return_time=None)  # 未归还的借书记录
        if not result.exists():
            context['msg'] = "该读者未借阅该图书！"
            return render(request, 'admin_return.html', context=context)
        result = result[0]
        if timezone.now() - result.return_date > timezone.timedelta(days=0):  # 逾期未还
            context['msg'] = "图书逾期归还，应该缴纳费用" + str((timezone.now() - result.return_date).days * 0.1) + "元"
        else:  # 期限内归还
            context['msg'] = "还书成功！图书期限内归还"
        book = Book_Table.objects.get(bid=bid)
        book.status = '未借出'
        book.save()
        result.return_time = timezone.now()  # 归还此书
        result.save()
        return render(request, 'admin_return.html', context=context)

