import os
import random
import io
import streamlit as st
from PIL import Image, ImageOps
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Global Constants for Layout
MAX_PAGE_WIDTH = 612
MAX_PAGE_HEIGHT = 792
PAGE_MARGIN = 30
TOP_BOTTOM_MARGIN = 25
ITEM_MARGIN = 25
ITEMS_PER_PAGE = 3

MAX_IMAGE_WIDTH = MAX_PAGE_WIDTH - (PAGE_MARGIN * 2)
MAX_IMAGE_HEIGHT = 500


def get_random_elements(root, n, seed=None):
    random_elements_per_category, categories_list = [], []

    if seed is None:
        seed = str(n) + "".join(
            [
                random.choice(["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"])
                for _ in range(5)
            ]
        )
    else:
        pass

    random.seed(seed)

    categories_folders = [
        os.path.join(root, d)
        for d in os.listdir(root)
        if os.path.isdir(os.path.join(root, d))
    ]

    categories_folders.sort()

    for category_folder in categories_folders:
        category = os.path.basename(category_folder)
        category_elements = [
            os.path.join(category_folder, file)
            for file in os.listdir(category_folder)
            if os.path.isfile(os.path.join(category_folder, file))
        ]
        category_elements_images = [
            img
            for img in category_elements
            if img.lower().endswith((".png", ".jpg", ".jpeg"))
        ]

        categories_list.append(category)
        num_samples = min(n, len(category_elements_images))
        random_elements_per_category.append(
            random.sample(category_elements_images, num_samples)
        )

    return random_elements_per_category, categories_list, seed


def get_resize_image(img):
    image = Image.open(img)
    image = ImageOps.exif_transpose(image)
    if image.height > MAX_IMAGE_HEIGHT or image.width > MAX_IMAGE_WIDTH:
        ratio = min(MAX_IMAGE_WIDTH / image.width, MAX_IMAGE_HEIGHT / image.height)
        new_width = int(image.width * ratio)
        new_height = int(image.height * ratio)
    else:
        new_width, new_height = image.width, image.height
    return new_width, new_height


def _get_layout_pages_for_category(category_images, placement_strategy_func):
    images_with_heights = []
    for img_path in category_images:
        _, height = get_resize_image(img_path)
        images_with_heights.append((img_path, height))

    images_with_heights.sort(key=lambda x: x[1], reverse=True)

    pages = []
    page_heights = []

    current_max_page_height = MAX_PAGE_HEIGHT - (TOP_BOTTOM_MARGIN * 2)

    for img_path, img_height in images_with_heights:
        placement_strategy_func(
            pages, page_heights, img_path, img_height, current_max_page_height
        )

    return pages


def _first_fit_placement(pages, page_heights, img_path, img_height, max_page_height):
    placed = False
    for i, page in enumerate(pages):
        if (
            len(page) < ITEMS_PER_PAGE
            and page_heights[i] + img_height + ITEM_MARGIN <= max_page_height
        ):
            page.append(img_path)
            page_heights[i] += img_height + ITEM_MARGIN
            placed = True
            break

    if not placed:
        pages.append([img_path])
        page_heights.append(img_height + ITEM_MARGIN)


def _best_fit_placement(pages, page_heights, img_path, img_height, max_page_height):
    best_fit_page = -1
    min_remaining_space = float("inf")

    for i, page in enumerate(pages):
        if (
            len(page) < ITEMS_PER_PAGE
            and page_heights[i] + img_height + ITEM_MARGIN <= max_page_height
        ):
            remaining_space = max_page_height - (
                page_heights[i] + img_height + ITEM_MARGIN
            )
            if remaining_space < min_remaining_space:
                min_remaining_space = remaining_space
                best_fit_page = i

    if best_fit_page != -1:
        pages[best_fit_page].append(img_path)
        page_heights[best_fit_page] += img_height + ITEM_MARGIN
    else:
        pages.append([img_path])
        page_heights.append(img_height + ITEM_MARGIN)


def get_final_layout(categories_list, seed):
    random.seed(seed)
    all_pages = []
    for category_images in categories_list:
        all_pages.extend(
            _get_layout_pages_for_category(category_images, _first_fit_placement)
        )
    return all_pages


def get_final_layout2(categories_list, seed):
    random.seed(seed)
    all_pages = []
    for category_images in categories_list:
        all_pages.extend(
            _get_layout_pages_for_category(category_images, _best_fit_placement)
        )
    return all_pages


def add_header(canvas_pdf, title, seed):
    canvas_pdf.setFont("Helvetica-Bold", 16)
    canvas_pdf.drawCentredString(
        MAX_PAGE_WIDTH / 2, MAX_PAGE_HEIGHT - 15 - 5, title.capitalize()
    )

    canvas_pdf.setLineWidth(1)
    canvas_pdf.line(
        PAGE_MARGIN,
        MAX_PAGE_HEIGHT - 15 - 10,
        MAX_PAGE_WIDTH - PAGE_MARGIN,
        MAX_PAGE_HEIGHT - 15 - 10,
    )

    canvas_pdf.setFont("Helvetica", 12)
    canvas_pdf.drawRightString(
        MAX_PAGE_WIDTH - PAGE_MARGIN, MAX_PAGE_HEIGHT - 15 - 5, f"Forma: {seed}"
    )

    canvas_pdf.setFont("Helvetica", 12)
    canvas_pdf.drawRightString(
        240, MAX_PAGE_HEIGHT - 15 - 5, "https://ensayosaleatorios.streamlit.app/"
    )


def add_pdf_page(canvas_pdf, layout_page, categories_list, seed):
    X_CENTER = PAGE_MARGIN

    title = ""
    if "random_elements_per_category" in st.session_state:
        for cat_name, cat_images in zip(
            categories_list, st.session_state.random_elements_per_category
        ):
            if layout_page and layout_page[0] in cat_images:
                title = cat_name
                break

    add_header(canvas_pdf, title, seed)

    y_cursor = 760
    for i, img_route in enumerate(layout_page):
        new_width, new_height = get_resize_image(img_route)

        y_cursor -= new_height
        canvas_pdf.drawImage(img_route, X_CENTER, y_cursor, new_width, new_height)

        y_cursor -= ITEM_MARGIN

        if i < len(layout_page) - 1:
            line_y = y_cursor + (ITEM_MARGIN / 2)
            canvas_pdf.setStrokeColorRGB(0.7, 0.7, 0.7)
            canvas_pdf.setLineWidth(0.5)
            canvas_pdf.setDash(3, 3)
            canvas_pdf.line(PAGE_MARGIN, line_y, MAX_PAGE_WIDTH - PAGE_MARGIN, line_y)

            canvas_pdf.setDash([])
            canvas_pdf.setStrokeColorRGB(0, 0, 0)


def create_pdf(layout_pages, categories_list, seed):
    buffer = io.BytesIO()
    PAGE_TYPE = letter

    canvas_pdf = canvas.Canvas(buffer, pagesize=PAGE_TYPE)
    canvas_pdf.setTitle("Ensayo " + seed)
    for layout_page in layout_pages:
        add_pdf_page(canvas_pdf, layout_page, categories_list, seed)
        canvas_pdf.showPage()

    canvas_pdf.save()
    buffer.seek(0)
    return buffer


if __name__ == "__main__":
    st.set_page_config(
        layout="centered", initial_sidebar_state="auto", page_title="Ensayos Aleatorios"
    )

    st.header("Ensayos Aleatorios", divider="green")
    st.subheader(
        "_En esta página web_ :blue[podrás crear ensayos aleatorios para preparar tu prueba] :red[PAES M1] :orange[2025] :sunglasses:"
    )

    options = [5, 10, 20]
    with st.container(border=True):
        st.header("Selecciona el número de preguntas por eje")
        with st.form("number_of_questions"):
            n = st.radio(
                "Seleccionar el número de preguntas",
                options=options,
                index=options.index(st.session_state.get("n", 5)),
                label_visibility="hidden",
            )
            submit_button_n = st.form_submit_button("Seleccionar")
            if submit_button_n:
                st.session_state["n"] = n

    with st.container(border=True):
        st.header(
            "Ingresa el número de forma (opcional, si se ingresa se omitirá la selección anterior)"
        )
        with st.form("seed_number"):
            input_seed = st.text_input(
                "Ingresar el número de la semilla (forma) para generar",
                placeholder="Escribe aquí un número",
                value=st.session_state.get("input_seed", ""),
                label_visibility="hidden",
            )
            submit_button_seed = st.form_submit_button("Seleccionar")
            if submit_button_seed:
                if input_seed.isdigit() and (
                    len(input_seed) == 6 or len(input_seed) == 7
                ):
                    valid_starts = [str(opt) for opt in options]

                    is_valid_start = False
                    parsed_n = None
                    for start_val in valid_starts:
                        if input_seed.startswith(start_val):
                            is_valid_start = True
                            parsed_n = int(start_val)
                            break

                    if is_valid_start:
                        st.success(f"Forma {input_seed} seleccionada")
                        st.session_state["input_seed"] = input_seed
                        st.session_state["n"] = parsed_n
                    else:
                        st.error(
                            f"El número de forma no es válido. Debe comenzar con {', '.join(valid_starts)}."
                        )
                        st.session_state["input_seed"] = ""
                else:
                    st.error(
                        "El número de forma no es válido. Debe ser un número de 6 o 7 dígitos."
                    )
                    st.session_state["input_seed"] = ""

    with st.container(border=True):
        st.header("Generar pdf")
        if st.button("Obtener pdf"):
            n_questions = st.session_state.get("n", 5)
            seed_input = st.session_state.get("input_seed", None)

            random_elements_per_category, categories_list, seed = get_random_elements(
                "./database", n_questions, seed_input
            )
            st.session_state["random_elements_per_category"] = (
                random_elements_per_category
            )

            layout_pages = get_final_layout2(random_elements_per_category, seed)
            pdf_buffer = create_pdf(layout_pages, categories_list, seed)

            st.session_state["seed"] = seed
            st.session_state["pdf_buffer"] = pdf_buffer

        if "pdf_buffer" in st.session_state:
            st.success(
                f"Se creó un ensayo con la forma: {st.session_state['seed']}. Ahora puedes descargarlo."
            )
            st.download_button(
                label="Descargar ensayo PDF",
                data=st.session_state["pdf_buffer"],
                file_name=f"ensayo_{st.session_state['seed']}.pdf",
                mime="application/pdf",
            )
