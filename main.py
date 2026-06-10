from gui import run
from tool.logger import get_logger

logger = get_logger(__name__)


def main():
    logger.info("アプリケーションを起動しました")
    run()
    logger.info("アプリケーションを終了します")


if __name__ == "__main__":
    main()
