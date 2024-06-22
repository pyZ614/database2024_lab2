from django.db import models


class Reader_Table(models.Model):  # 读者信息
    rid = models.AutoField(primary_key=True)  # 读者ID
    psw = models.CharField(max_length=256)  # 读者密码
    rname = models.CharField(max_length=10)  # 姓名
    phone = models.CharField(max_length=20)  # 电话
    email = models.CharField(max_length=50)  # 邮箱


class Admin_Table(models.Model):  # 图书管理员信息
    aid = models.CharField(max_length=10, primary_key=True)  # 工号，格式：gh001
    psw = models.CharField(max_length=256)  # 管理员密码
    aname = models.CharField(max_length=10)  # 姓名


class Bname_Table(models.Model):  # 书目信息
    isbn = models.CharField(max_length=50, primary_key=True)  # ISBN号
    bname = models.CharField(max_length=50)  # 书名
    author = models.CharField(max_length=50)  # 作者
    pub = models.CharField(max_length=50)  # 出版商
    pubtime = models.DateTimeField()  # 出版年月
    # cs = models.IntegerField()   # 册数
    admin = models.ForeignKey(Admin_Table, on_delete=models.CASCADE)  # 经办人
    book_image = models.ImageField(upload_to='book', blank=True, null=True)  # 图书图片


class Book_Table(models.Model):  # 图书信息
    bid = models.AutoField(primary_key=True)  # 图书id
    isbn = models.ForeignKey(Bname_Table, on_delete=models.CASCADE)  # ISBN号
    status = models.CharField(max_length=20)  # 状态（未借出、已借出、已预约）
    admin = models.ForeignKey(Admin_Table, on_delete=models.CASCADE)  # 经办人

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        assert self.status in ('未借出', '已借出', '已预约'), '书本状态必须是未借出、已借出、已预约'
        super(Book_Table, self).save(force_insert, force_update, using, update_fields)

    def delete(self, using=None, keep_parents=False):
        assert self.status != '已借出', '已借出图书不允许出库'
        super(Book_Table, self).delete(using, keep_parents)


class Borrow_Table(models.Model):  # 借书信息
    rid = models.ForeignKey(Reader_Table, on_delete=models.CASCADE)  # 读者ID
    bid = models.ForeignKey(Book_Table, on_delete=models.CASCADE)  # 图书ID
    borrow_time = models.DateTimeField()  # 借阅时间
    return_date = models.DateTimeField()  # 应还时间
    return_time = models.DateTimeField(blank=True, null=True)  # 归还时间

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        assert self.borrow_time < self.return_date, '归还时间应在借阅时间之后'
        super(Borrow_Table, self).save(force_insert, force_update, using, update_fields)
    class Meta:
        unique_together = ("rid", "bid", "borrow_time") # 确保在数据库中的组合是唯一的，防止重复记录。


class Reserve_Table(models.Model):  # 预约信息
    rid = models.ForeignKey(Reader_Table, on_delete=models.CASCADE)  # 读者ID
    isbn = models.ForeignKey(Bname_Table, on_delete=models.CASCADE)  # ISBN号
    bid = models.ForeignKey(Book_Table, blank=True, null=True, on_delete=models.CASCADE)  # 图书ID
    reserve_time = models.DateTimeField()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):  # 创建预约触发器
        super(Reserve_Table, self).save(force_insert, force_update, using, update_fields)
    class Meta:
        unique_together = ("rid", "isbn", "reserve_time")