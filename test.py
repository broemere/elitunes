import logging
root_dir = '/media/eli/shorty/music/'
static_dir='static/'
cfg_dir = root_dir + 'cfg/'
logging.basicConfig(filename=str(cfg_dir + "debug.log"), level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logging.info("TEST1")

while True:
    num = 1
