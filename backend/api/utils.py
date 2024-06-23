from django.conf import settings
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from recipes.models import Ingredient


def shopping_cart_to_pdf(response, cart):
    pdf = canvas.Canvas(response)
    pdfmetrics.registerFont(
        TTFont(
            'ArialRegular',
            f'{str(settings.BASE_DIR)}/data/ArialRegular.ttf'
        )
    )
    pdf.setFont('ArialRegular', 32)
    pdf.drawString(15, 800, 'Список покупок: ')
    pdf.setFont('ArialRegular', 15)
    row_step = 750
    for item in cart:
        ingredient = Ingredient.objects.get(
            id=item['ingredient']
        )
        amount = item['amount']
        shopping_row = (
            f'{ingredient.name}: {amount}, '
            f'{ingredient.measurement_unit}'
        )
        pdf.drawString(15, row_step, f' - {shopping_row}')
        row_step -= 20
    pdf.showPage()
    pdf.save()
    return response
