import logging


def init_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    # create file and stream handlers and set level to debug
    fh = logging.FileHandler(filename='../logfile.log')
    sh = logging.StreamHandler()
    fh.setLevel(logging.WARNING)
    sh.setLevel(logging.DEBUG)
    # create formatter
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s (%(filename)s:%(lineno)d)")
    # add formatter to fh and sh
    fh.setFormatter(formatter)
    sh.setFormatter(formatter)
    # add fh and sh to logger
    logger.addHandler(fh)
    logger.addHandler(sh)
    logger.propagate = False
    return logger
