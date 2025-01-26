from deployflow.core import colors
from deployflow.logger import logger


def fatal(error):
    logger.error(error)
    print(colors.BOLD + colors.RED + error + colors.ENDC)
    exit(1)
