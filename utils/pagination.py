class Pagination:
    def __init__(self, page, per_page, total_items):
        self.page = page
        self.per_page = per_page
        self.total_items = total_items
        self.total_pages = (total_items + per_page - 1) // per_page
        
    @property
    def has_prev(self):
        return self.page > 1
        
    @property
    def has_next(self):
        return self.page < self.total_pages
        
    @property
    def prev_num(self):
        return self.page - 1
        
    @property
    def next_num(self):
        return self.page + 1
        
    def iter_pages(self):
        # 简单的页码生成逻辑
        for i in range(1, self.total_pages + 1):
            if i <= 2 or i >= self.total_pages - 1 or abs(i - self.page) <= 2:
                yield i
            elif abs(i - self.page) == 3:
                yield None 