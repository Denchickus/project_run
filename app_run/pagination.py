from rest_framework.pagination import PageNumberPagination

class CustomPageNumberPagination(PageNumberPagination):
    # Параметр "size" в URL будет определять,
    # сколько объектов показывать на одной странице
    page_size_query_param = 'size'
