import typer

from . import config
from .scraper import Scraper

app = typer.Typer()

__all__ = ['run']

@app.command()
def collect_book_info(
    keyword: str = typer.Argument(''),
) -> None:
    config.assign('keyword', keyword)
    scraper = Scraper()
    pass

@app.command()
def search(
    keyword: str = typer.Argument(''),
) -> None:
    config.assign('keyword', keyword)
    scraper = Scraper()
    scraper.get_all_book_profile_page_urls()

def run() -> None:
    config.init()
    config.config_logging()
    app()

if __name__ == '__main__':
    run()