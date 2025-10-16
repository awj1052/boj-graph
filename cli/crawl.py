import argparse
from services import CrawlerFactory


def main():
    parser = argparse.ArgumentParser(description='BOJ Status Crawler')
    parser.add_argument('url', help='Contest status URL')
    parser.add_argument('-o', '--output', default='status.jsonl', help='Output JSONL file path')
    parser.add_argument('-c', '--cookie', help='BOJ_AUTO_LOGIN cookie value')
    parser.add_argument('-m', '--max-pages', type=int, help='Maximum pages to crawl')
    parser.add_argument('--no-cache', action='store_true', help='Disable cache')
    args = parser.parse_args()

    crawler = CrawlerFactory.create(
        bojautologin=args.cookie,
        use_cache=not args.no_cache
    )

    crawler.crawl(args.url, args.output, args.max_pages)
    print(f"Crawling completed: {args.output}")


if __name__ == '__main__':
    main()
