"""HTML fixture data for testing parsers.

This module contains actual HTML snippets extracted from bookvoed.ru
for realistic testing of parser behavior.
"""

# Sample book page HTML with complete structure
BOOK_PAGE_HTML = '''
<div class="product-title-author">
    <h1 class="product-title-author__title">Мастер и Маргарита</h1>
</div>

<div class="price-block-price-info">
    <div class="price-block-price-info__price">
        <span>499 ₽</span>
        <span>799 ₽</span>
    </div>
    <div class="price-block-price-info__discount">
        Скидка 38%
    </div>
</div>

<div class="price-block-availability order-info-price-block__availability">
    В наличии
</div>

<div class="product-characteristics-full">
    <table>
        <tr class="product-characteristics-full__row">
            <th class="product-characteristics-full__cell-th">Автор</th>
            <td class="product-characteristics-full__cell-td">Булгаков М.А.</td>
        </tr>
        <tr class="product-characteristics-full__row">
            <th class="product-characteristics-full__cell-th">Жанр</th>
            <td class="product-characteristics-full__cell-td">
                <ul>
                    <li>Классическая проза</li>
                    <li>Роман</li>
                    <li>Мистика</li>
                </ul>
            </td>
        </tr>
        <tr class="product-characteristics-full__row">
            <th class="product-characteristics-full__cell-th">Издательство</th>
            <td class="product-characteristics-full__cell-td">Эксмо</td>
        </tr>
        <tr class="product-characteristics-full__row">
            <th class="product-characteristics-full__cell-th">Кол-во страниц</th>
            <td class="product-characteristics-full__cell-td">416</td>
        </tr>
        <tr class="product-characteristics-full__row">
            <th class="product-characteristics-full__cell-th">Вес</th>
            <td class="product-characteristics-full__cell-td">0.45 кг</td>
        </tr>
        <tr class="product-characteristics-full__row">
            <th class="product-characteristics-full__cell-th">Тираж</th>
            <td class="product-characteristics-full__cell-td">10\xa0000</td>
        </tr>
    </table>
</div>

<script type="application/ld+json">
{
    "@context": "https://schema.org",
    "@graph": [
        {
            "@type": "Book",
            "name": "Мастер и Маргарита",
            "description": "Знаменитый роман Михаила Булгакова",
            "genre": "Классическая проза",
            "numberOfPages": 416,
            "publisher": "Эксмо",
            "datePublished": "2020",
            "bookFormat": "https://schema.org/Hardcover",
            "aggregateRating": {
                "ratingValue": 4.9,
                "reviewCount": 1250
            }
        }
    ]
}
</script>
'''

# Sample catalog page HTML with book cards
CATALOG_PAGE_HTML = '''
<div class="product-list app-catalog__products">
    <div class="product-card">
        <a href="/book/123" class="product-card__image-link base-link">
            <img src="/img/book1.jpg" />
        </a>
        <div class="product-card__title">Книга 1</div>
    </div>
    <div class="product-card">
        <a href="/book/456" class="product-card__image-link base-link">
            <img src="/img/book2.jpg" />
        </a>
        <div class="product-card__title">Книга 2</div>
    </div>
    <div class="product-card">
        <a href="/book/789" class="product-card__image-link base-link">
            <img src="/img/book3.jpg" />
        </a>
        <div class="product-card__title">Книга 3</div>
    </div>
</div>
<div class="pagination">
    <a href="?page=2">2</a>
    <a href="?page=3">3</a>
    <a href="?page=4">Далее</a>
</div>
'''

# Empty catalog page (no books)
CATALOG_PAGE_EMPTY_HTML = '''
<div class="some-other-content">
    <p>Нет товаров</p>
</div>
'''

# Catalog page with next page button
CATALOG_PAGE_WITH_NEXT_BUTTON = '''
<div class="product-list app-catalog__products">
    <div class="product-card">
        <a href="/book/123" class="product-card__image-link base-link">Книга</a>
    </div>
</div>
<div class="pagination">
    <a href="?page=2">Следующая</a>
</div>
'''

# Book page with pre-order instead of availability
BOOK_PAGE_PREORDER_HTML = '''
<div class="product-title-author">
    <h1 class="product-title-author__title">Новая книга</h1>
</div>
<div class="price-block-price-info">
    <div class="price-block-price-info__price">
        <span>899 ₽</span>
    </div>
</div>
<div class="price-block-preorder">
    Предзаказ
</div>
<div class="product-characteristics-full">
    <table>
        <tr class="product-characteristics-full__row">
            <th class="product-characteristics-full__cell-th">Автор</th>
            <td class="product-characteristics-full__cell-td">Иванов И.И.</td>
        </tr>
    </table>
</div>
'''

# Book page with "low stock" indication
BOOK_PAGE_LOW_STOCK_HTML = '''
<div class="price-block-availability order-info-price-block__availability">
    Осталось мало
</div>
'''

# JSON-LD only test (no characteristics table)
BOOK_PAGE_JSONLD_ONLY_HTML = '''
<script type="application/ld+json">
{
    "@context": "https://schema.org",
    "@type": "Book",
    "name": "Тестовая книга",
    "description": "Тестовое описание",
    "genre": "Тестовый жанр",
    "numberOfPages": 300,
    "publisher": "ТестИздат",
    "datePublished": "2023",
    "bookFormat": "https://schema.org/Paperback"
}
</script>
'''

# Complex price block with multiple spans
BOOK_PAGE_COMPLEX_PRICE_HTML = '''
<div class="price-block-price-info">
    <div class="price-block-price-info__price">
        <span>1 299 ₽</span>
        <span>1 999 ₽</span>
        <span>Спеццена</span>
    </div>
    <div class="price-block-price-info__discount">
        Скидка 35%
    </div>
</div>
'''

# Weight in kilograms (decimal)
BOOK_PAGE_WEIGHT_KG_HTML = '''
<div class="product-characteristics-full">
    <table>
        <tr class="product-characteristics-full__row">
            <th class="product-characteristics-full__cell-th">Вес</th>
            <td class="product-characteristics-full__cell-td">0.75 кг</td>
        </tr>
    </table>
</div>
'''

# Missing price block
BOOK_PAGE_NO_PRICE_HTML = '''
<div class="product-title-author">
    <h1 class="product-title-author__title">Книга без цены</h1>
</div>
<div class="product-characteristics-full">
    <table>
        <tr class="product-characteristics-full__row">
            <th class="product-characteristics-full__cell-th">Первый автор</th>
            <td class="product-characteristics-full__cell-td">Второй автор</td>
        </tr>
    </table>
</div>
'''
