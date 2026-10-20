"""Cálculo fiscal y generación de facturas PDF para Healthy Fast."""

import os
import uuid
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


CENTAVO = Decimal("0.01")
IVA_PORCENTAJE = Decimal("19.00")


def _dinero(valor):
    return Decimal(str(valor or 0)).quantize(CENTAVO, rounding=ROUND_HALF_UP)


def calcular_factura(
    items,
    comprador,
    medio_pago,
    numero_factura,
    descuento_porcentaje=Decimal("0"),
    fecha_emision=None,
):
    """Valida líneas y calcula todos los valores desde los precios del servidor."""
    if not items:
        raise ValueError("La factura debe tener al menos un producto.")

    descuento_porcentaje = Decimal(str(descuento_porcentaje))
    if descuento_porcentaje < 0 or descuento_porcentaje > 1:
        raise ValueError("El porcentaje de descuento no es válido.")

    lineas_base = []
    for item in items:
        try:
            cantidad = int(item.get("cantidad", 0))
            precio = _dinero(item.get("precio"))
        except (TypeError, ValueError, ArithmeticError) as error:
            raise ValueError("La cantidad o el precio del producto no son válidos.") from error
        if cantidad < 1 or precio <= 0:
            raise ValueError("La cantidad y el precio deben ser mayores que cero.")

        lineas_base.append({
            "id_producto": item.get("id"),
            "codigo": str(item.get("id") or "N/A"),
            "nombre": str(item.get("nombre") or "Producto"),
            "unidad": "UND",
            "cantidad": cantidad,
            "precio_unitario": precio,
            "bruto": _dinero(precio * cantidad),
        })

    subtotal = _dinero(sum((linea["bruto"] for linea in lineas_base), Decimal("0")))
    descuento = _dinero(subtotal * descuento_porcentaje)
    descuento_pendiente = descuento
    lineas = []

    for indice, linea in enumerate(lineas_base):
        if indice == len(lineas_base) - 1:
            descuento_linea = descuento_pendiente
        elif subtotal:
            descuento_linea = _dinero(descuento * linea["bruto"] / subtotal)
            descuento_linea = min(descuento_linea, descuento_pendiente)
        else:
            descuento_linea = Decimal("0.00")
        descuento_pendiente -= descuento_linea

        base_gravable = linea["bruto"] - descuento_linea
        iva_linea = _dinero(base_gravable * IVA_PORCENTAJE / Decimal("100"))
        lineas.append({
            **linea,
            "descuento": descuento_linea,
            "iva_porcentaje": IVA_PORCENTAJE,
            "iva": iva_linea,
            "total": base_gravable + iva_linea,
        })

    total_impuestos = _dinero(sum((linea["iva"] for linea in lineas), Decimal("0")))
    total_neto = _dinero(subtotal - descuento + total_impuestos)
    emision = fecha_emision or date.today()
    medio_pago_etiqueta = {
        "efectivo": "Efectivo contra entrega",
        "transferencia": "Transferencia pendiente de validación",
    }.get(medio_pago, str(medio_pago or "No informado").title())

    return {
        "numero_factura": numero_factura,
        "codigo_unico": str(uuid.uuid4()),
        "fecha_emision": emision,
        "fecha_vencimiento": emision,
        "forma_pago": "Contado",
        "medio_pago": medio_pago_etiqueta,
        "tipo_operacion": "Venta nacional de bienes",
        "moneda": "COP",
        "comprador": {
            "nombre": str(comprador.get("nombre_completo") or "").strip(),
            "tipo_documento": str(comprador.get("tipo_documento") or ""),
            "documento": str(comprador.get("documento") or ""),
            "pais": str(comprador.get("pais") or "Colombia"),
            "departamento": str(comprador.get("departamento") or ""),
            "ciudad": str(comprador.get("ciudad") or ""),
            "direccion": str(comprador.get("direccion") or ""),
            "telefono": str(comprador.get("telefono") or ""),
            "email": str(comprador.get("email") or ""),
        },
        "vendedor": {
            "razon_social": os.getenv("HEALTHYFAST_RAZON_SOCIAL", "Healthy Fast"),
            "nit": os.getenv("HEALTHYFAST_NIT", "Por configurar"),
            "pais": os.getenv("HEALTHYFAST_PAIS", "Colombia"),
            "departamento": os.getenv("HEALTHYFAST_DEPARTAMENTO", "Por configurar"),
            "ciudad": os.getenv("HEALTHYFAST_CIUDAD", "Por configurar"),
            "direccion": os.getenv("HEALTHYFAST_DIRECCION", "Por configurar"),
            "telefono": os.getenv("HEALTHYFAST_TELEFONO", "Por configurar"),
            "email": os.getenv("HEALTHYFAST_EMAIL", "fasthealthy40@gmail.com"),
        },
        "lineas": lineas,
        "subtotal": subtotal,
        "descuento": descuento,
        "total_bruto": subtotal,
        "iva_porcentaje": IVA_PORCENTAJE,
        "iva": total_impuestos,
        "total_impuestos": total_impuestos,
        "total_neto": total_neto,
        "total_final": total_neto,
    }


def _formato_cop(valor):
    numero = _dinero(valor)
    return f"$ {numero:,.2f} COP".replace(",", "X").replace(".", ",").replace("X", ".")


def generar_pdf_factura(factura):
    """Genera la factura en memoria para descarga o impresión desde el navegador."""
    salida = BytesIO()
    documento = SimpleDocTemplate(
        salida,
        pagesize=letter,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=14 * mm,
        bottomMargin=16 * mm,
        title=f"Factura {factura['numero_factura']}",
        author=factura["vendedor"]["razon_social"],
    )
    estilos = getSampleStyleSheet()
    estilos.add(ParagraphStyle(
        name="InvoiceTitle", parent=estilos["Title"], fontName="Helvetica-Bold",
        fontSize=21, leading=24, textColor=colors.HexColor("#721c24"), alignment=TA_RIGHT,
    ))
    estilos.add(ParagraphStyle(
        name="InvoiceSmall", parent=estilos["BodyText"], fontSize=8, leading=11,
        textColor=colors.HexColor("#475569"),
    ))
    estilos.add(ParagraphStyle(
        name="InvoiceRight", parent=estilos["InvoiceSmall"], alignment=TA_RIGHT,
    ))
    estilos.add(ParagraphStyle(
        name="InvoiceCell", parent=estilos["InvoiceSmall"], fontSize=7.2, leading=9,
    ))
    historia = []
    vendedor = factura["vendedor"]
    comprador = factura["comprador"]
    datos_vendedor = (
        f"<b>{escape(vendedor['razon_social'])}</b><br/>NIT: {escape(vendedor['nit'])}<br/>"
        f"{escape(vendedor['direccion'])}<br/>{escape(vendedor['ciudad'])}, "
        f"{escape(vendedor['departamento'])}, {escape(vendedor['pais'])}<br/>"
        f"Tel. {escape(vendedor['telefono'])}<br/>{escape(vendedor['email'])}"
    )
    datos_documento = (
        f"<b>Factura de venta</b><br/>Número: {escape(factura['numero_factura'])}<br/>"
        f"Emisión: {factura['fecha_emision']}<br/>Vencimiento: {factura['fecha_vencimiento']}<br/>"
        f"Forma de pago: {escape(factura['forma_pago'])}<br/>"
        f"Medio: {escape(factura['medio_pago'])}<br/>"
        f"Operación: {escape(factura['tipo_operacion'])}<br/>"
        f"Identificador único: {escape(factura['codigo_unico'])}"
    )
    encabezado = Table(
        [[Paragraph(datos_vendedor, estilos["InvoiceSmall"]), Paragraph("FACTURA", estilos["InvoiceTitle"])],
         [Paragraph(datos_documento, estilos["InvoiceSmall"]), Paragraph("MONEDA: COP", estilos["InvoiceRight"]) ]],
        colWidths=[108 * mm, 77 * mm],
    )
    encabezado.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("LINEBELOW", (0, 1), (-1, 1), 1, colors.HexColor("#721c24")),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 9),
    ]))
    historia.extend([encabezado, Spacer(1, 8 * mm)])

    datos_comprador = (
        f"<b>{escape(comprador['nombre'])}</b><br/>"
        f"{escape(comprador['tipo_documento'])}: {escape(comprador['documento'])}<br/>"
        f"{escape(comprador['direccion'])}<br/>{escape(comprador['ciudad'])}, "
        f"{escape(comprador['departamento'])}, {escape(comprador['pais'])}<br/>"
        f"Tel. {escape(comprador['telefono'])}<br/>{escape(comprador['email'])}"
    )
    comprador_tabla = Table(
        [[Paragraph("DATOS DEL COMPRADOR", estilos["InvoiceSmall"])],
         [Paragraph(datos_comprador, estilos["InvoiceSmall"])]],
        colWidths=[185 * mm],
    )
    comprador_tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    historia.extend([comprador_tabla, Spacer(1, 7 * mm)])

    estilos.add(ParagraphStyle(
        name="InvoiceHeader", parent=estilos["InvoiceCell"], textColor=colors.white,
        fontName="Helvetica-Bold",
    ))
    encabezados = ["N.º / Código", "Descripción", "Unidad", "Cant.", "Precio unit.", "Descuento", "IVA", "Precio venta"]
    filas = [[Paragraph(escape(texto), estilos["InvoiceHeader"]) for texto in encabezados]]
    for indice, linea in enumerate(factura["lineas"], start=1):
        filas.append([
            Paragraph(f"{indice}<br/>{escape(linea['codigo'])}", estilos["InvoiceCell"]),
            Paragraph(escape(linea["nombre"]), estilos["InvoiceCell"]),
            linea["unidad"],
            str(linea["cantidad"]),
            _formato_cop(linea["precio_unitario"]),
            _formato_cop(linea["descuento"]),
            Paragraph(f"{linea['iva_porcentaje']}%<br/>{_formato_cop(linea['iva'])}", estilos["InvoiceCell"]),
            _formato_cop(linea["total"]),
        ])
    tabla_lineas = Table(
        filas,
        colWidths=[18 * mm, 43 * mm, 13 * mm, 12 * mm, 27 * mm, 24 * mm, 25 * mm, 23 * mm],
        repeatRows=1,
        hAlign="LEFT",
    )
    tabla_lineas.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#721c24")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    historia.extend([tabla_lineas, Spacer(1, 5 * mm)])

    totales = [
        ["Subtotal", _formato_cop(factura["subtotal"])],
        ["Descuento", _formato_cop(factura["descuento"])],
        ["Total bruto", _formato_cop(factura["total_bruto"])],
        [f"IVA ({factura['iva_porcentaje']}%)", _formato_cop(factura["iva"])],
        ["Total de impuestos", _formato_cop(factura["total_impuestos"])],
        ["Total neto", _formato_cop(factura["total_neto"])],
        ["TOTAL FACTURA COP", _formato_cop(factura["total_final"])],
    ]
    tabla_totales = Table(totales, colWidths=[50 * mm, 40 * mm], hAlign="RIGHT")
    tabla_totales.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.HexColor("#721c24")),
        ("TEXTCOLOR", (0, -1), (-1, -1), colors.HexColor("#721c24")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    historia.extend([tabla_totales, Spacer(1, 6 * mm)])
    historia.append(Paragraph(
        "Documento generado por Healthy Fast a partir de los datos registrados en la compra. "
        "Identificador interno; no sustituye la validación de factura electrónica DIAN.",
        estilos["InvoiceSmall"],
    ))
    documento.build(historia)
    salida.seek(0)
    return salida