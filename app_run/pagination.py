from rest_framework.pagination import PageNumberPagination

"""Кастомная пагинация API."""


class CustomPageNumberPagination(PageNumberPagination):
    """Пагинация с возможностью указать размер страницы через параметр size."""

    page_size_query_param = "size"
