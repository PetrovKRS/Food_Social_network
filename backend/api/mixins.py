class CheckIntOrStrMixin:
    """ Проверка, что pk в эндпоинте является числом. """

    def validate_pk(self, pk):
        try:
            int(pk)
            return True
        except ValueError:
            return False
