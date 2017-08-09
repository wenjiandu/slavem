import datetime
import logging


class Task(object):
    """
    定时任务实例
    """

    def __init__(self, name, type, lanuch, delay, host, des, off):
        # 需要保存到MongoDB的参数
        self.name = name
        self.type = type
        self.lanuch = datetime.datetime.strptime(lanuch, '%H:%M:%S').time()
        self.delay = delay  # min
        self.host = host
        self.des = des  # 备注描述
        self.off = off
        # ====================
        self.toMongoDbArgs = ['name', 'type', 'lanuch', 'delay', 'host', 'des', 'off']

        self.log = logging.getLogger('slavem')

        self.lanuchTime = datetime.datetime.now()
        self.deadline = datetime.datetime.now()
        self.refreshDeadline()

        self.isLate = False

    def toMongoDB(self):
        """
        生成用于保存到 MongoDB 的任务
        :return:
        """
        dic = {k: self.__dict__[k] for k in self.toMongoDbArgs}
        dic['lanuch'] = self.lanuch.strftime('%H:%M:%S')
        return dic

    def __str__(self):
        s = super(Task, self).__str__()
        s.strip('>')
        s += ' '
        for k, v in self.__dict__.items():
            s += '{}:{} '.format(k, v)
        s += '>'
        return s

    def refreshDeadline(self):
        """
        截止时间
        :return:
        """
        self.deadline = self.getDeadline()
        # 计算开始时间
        lanuchTime = datetime.datetime.combine(self.deadline.date(), self.lanuch)

        if lanuchTime > self.deadline:
            # 跨天了
            lanuchTime -= datetime.timedelta(days=1)

        self.lanuchTime = lanuchTime

    def getDeadline(self):
        """

        :return:
        """
        now = datetime.datetime.now()
        lanuchTime = datetime.datetime.combine(now.date(), self.lanuch)
        deadline = lanuchTime + datetime.timedelta(seconds=60 * self.delay)

        if deadline < now:
            # 现在已经过了截止日期了，时间推迟到次日
            deadline += datetime.timedelta(days=1)

        return deadline

    def isReport(self, report):
        """
        检查是否是对应的 reposrt
        :param report:  dict()
        :return:
        """

        if self.name != report['name']:
            r, diff = False, 'name'
        elif self.type != report['type']:
            r, diff = False, 'type'
        elif self.host != report['host']:
            r, diff = False, 'host'
        elif self.lanuchTime > report['datetime'] or report['datetime'] > self.deadline:
            r, diff = False, 'datetime'
        else:
            r, diff = True, None

        if __debug__ and not r:
            rv = report[diff]
            sv = getattr(self, diff)
            self.log.debug(u'报告 {sv} 不匹配 {rv}'.format(sv=sv, rv=rv))

        return r

    def finishAndRefresh(self):
        """
        今天的任务完成了，刷新
        :return:
        """
        self.refreshDeadline()
        self.isLate = False

    def delayDeadline(self, seconds=60):
        """
        没有收到汇报,推迟 deadline
        :return:
        """
        self.deadline += datetime.timedelta(seconds=seconds)

    def setLate(self):
        self.isLate = True

    def toNotice(self):
        """

        :return:
        """
        return self.__dict__.copy()

    def toSameTaskKV(self):
        return {
            'name': self.name,
            'type': self.type,
            'lanuch': self.lanuch.strftime('%H:%M:%S'),
        }

    def __eq__(self, other):
        return self.toSameTaskKV() == other.toSameTaskKV()
