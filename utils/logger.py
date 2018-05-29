import os
import logging
import logging.handlers 

class Logger(object):
    """Init Author: flyer <flyer103@gmail.com>"""


    @staticmethod
    def get_logger(service='', level=logging.DEBUG):
        """需要确保 service 唯一"""

        logger = logging.getLogger(service)
        logger.setLevel(level)

        handlers = Logger.get_handlers()
        for handler in handlers:
            logger.addHandler(handler)

        return logger

    @staticmethod
    def get_formatter(service=''):
        formatter = logging.Formatter(
            fmt='[%(name)s][%(asctime)s][%(levelname)s][%(filename)s][%(threadName)s][%(funcName)s][%(lineno)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )

        return formatter
    
    @staticmethod
    def get_handlers(fname='logger.log', **kwargs):
        """提供两类 handler，一类在终端打印，一类写入到文件中.

        参数:
        + fname: 日志写入的文件名，默认 'logger.log'
        + level_stream: stream logging 的级别，默认 DEBUG
        + level_trfile: time rotating filie logging 的级别，默认 WARNING
        + when_trfile: 日志滚动形式，默认 'W0'
        + encoding: 日志写入的编码，默认 'utf-8'

        XXX:
          + 参数检验
        """
        fname = fname or 'logger.log'
        level_stream = kwargs.get('level_stream', logging.DEBUG)
        level_trfile = kwargs.get('level_trfile', logging.INFO)
        when_trfile = kwargs.get('when_trfile', 'W0')
        encoding = kwargs.get('encoding', 'utf-8')
        
        absdir = os.path.abspath(__file__).rsplit('/', 2)[0]
        dir_log = os.path.join(absdir, 'log')

        if not os.path.exists(dir_log):
            os.makedirs(dir_log)

        logfile_warning = os.path.join(dir_log, fname)

        formatter = Logger.get_formatter()

        # streaming handler        
        handler_stream = logging.StreamHandler()
        handler_stream.setLevel(level_stream)
        handler_stream.setFormatter(formatter)

        # timed rotating file handler for waring+
        handler_tf_warn = logging.handlers.TimedRotatingFileHandler(logfile_warning,
                                                                    when=when_trfile,
                                                                    encoding=encoding)
        handler_tf_warn.setLevel(level_trfile)
        handler_tf_warn.setFormatter(formatter)

        return [handler_stream, handler_tf_warn]

