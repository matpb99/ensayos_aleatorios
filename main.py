import os
import random
import io
import streamlit as st
from PIL import Image, ImageOps
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def get_random_elements(root, n, seed=None):

    random_elements_per_category, categories_list = [],[]

    if seed == None:
        seed = "".join([random.choice(['1','2','3','4','5','6','7','8','9','0']) for _ in range(6)])
        random.seed(seed)
    else:
        random.seed(seed)

    categories_folders = [os.path.join(root, d) for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))]

    for category_folder in categories_folders:
        category = os.path.basename(category_folder)
        category_elements = [os.path.join(category_folder, file) for file in os.listdir(category_folder) if os.path.isfile(os.path.join(category_folder, file))]
        category_elements_images = [img for img in category_elements if img.lower().endswith(('.png', '.jpg', '.jpeg'))]

        categories_list += [category]
        random_elements_per_category += [random.sample(category_elements_images, n)]
    
    return random_elements_per_category, categories_list, seed

def get_resize_data(image_list):
    MAX_WIDTH = 612 - (30*2)
    MAX_HEIGHT = 500
    new_size_images_list = []

    for img in image_list:
        image = Image.open(img)
        if image.height > MAX_HEIGHT or image.width > MAX_WIDTH:
            ratio = min(MAX_WIDTH / image.width, MAX_HEIGHT / image.height)
            new_height = int(image.height * ratio)
        else:
            new_height = image.height

        new_size_images_list.append(new_height)
    
    return new_size_images_list

def get_resize_image(img):
    MAX_WIDTH = 612 - (30*2)
    MAX_HEIGHT = 500
    image = Image.open(img)
    image = ImageOps.exif_transpose(image) 
    if image.height > MAX_HEIGHT or image.width > MAX_WIDTH:
        ratio = min(MAX_WIDTH / image.width, MAX_HEIGHT / image.height)
        new_width = int(image.width * ratio)
        new_height = int(image.height * ratio)
    else:
        new_width, new_height = image.width, image.height
    return new_width, new_height

def optimize_layout(left_nodes, actual_page, actual_layout, final_layout_candidates):
    ITEMS_PER_PAGE = 3
    MARGIN_ITEMS = 25
    MAX_HEIGHT = 792 - 25 - MARGIN_ITEMS

    if len(left_nodes)==0:
        final_layout_candidates.append(actual_layout)
    
    else:
        size_left_nodes = get_resize_data(left_nodes)

        size_actual_page = get_resize_data(actual_page)

        if len(actual_layout) == 0:
            replace_flag = False
        else:
            actual_page = actual_layout[-1]
            replace_flag = True

        add_node_flag = False
        for item_index in range(len(left_nodes)):
            if sum(size_actual_page) + size_left_nodes[item_index] <= MAX_HEIGHT - (len(actual_page)*MARGIN_ITEMS) and len(actual_page)<=ITEMS_PER_PAGE-1: 
                actual_page += [left_nodes[item_index]]
                left_nodes.pop(left_nodes.index(left_nodes[item_index]))
                add_node_flag = True 
                break

        if add_node_flag == True:
            if replace_flag == True:
                actual_layout[-1] = actual_page
            else:
                actual_layout.append(actual_page)
        else:
            value = random.choice(left_nodes) 
            index = left_nodes.index(value)

            actual_layout.append([value])
            left_nodes.pop(index)
            actual_page = [value]       
        optimize_layout(left_nodes, actual_page, actual_layout, final_layout_candidates)

def get_final_layout(categories_list, seed):
    final = []
    random.seed(seed)
    for category in categories_list:

        layout_proposals_per_category = []

        for _ in range(10):
            for file in category:
                left_nodes = category.copy()
                item_index = left_nodes.index(file)
                left_nodes.pop(item_index)
                optimize_layout(left_nodes, [file], [], layout_proposals_per_category)
        
        min_layout = min(layout_proposals_per_category, key=len)
        final += min_layout
        
    return final

def add_header(canvas_pdf, title, seed):
    PAGE_WIDTH = 612
    PAGE_HEIGHT = 792 - 15
    
    canvas_pdf.setFont("Helvetica-Bold", 16)
    canvas_pdf.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT-5, title.capitalize())

    canvas_pdf.setLineWidth(1)
    canvas_pdf.line(30, PAGE_HEIGHT - 10, PAGE_WIDTH - 30, PAGE_HEIGHT - 10) 

    canvas_pdf.setFont("Helvetica", 12)
    canvas_pdf.drawRightString(PAGE_WIDTH - 30, PAGE_HEIGHT -5, f"Forma: {seed}")

    canvas_pdf.setFont("Helvetica", 12)
    canvas_pdf.drawRightString(PAGE_WIDTH/3, PAGE_HEIGHT -5, f"https://ensayosaleatorios.streamlit.app/")

def add_pdf_page(canvas_pdf, layout_page, categories_list, seed):
    X_CENTER = 30
    MARGIN = 25
    for item in categories_list:
        if item in layout_page[0]:
                title = item
                break
    add_header(canvas_pdf, title, seed)

    space_left = 792 - 25 - MARGIN
    for img_route in layout_page:
        new_width, new_height = get_resize_image(img_route)
        canvas_pdf.drawImage(img_route, X_CENTER, space_left - new_height - 5, new_width, new_height)
        canvas_pdf.setStrokeColorRGB(0, 0, 0) 
        canvas_pdf.setLineWidth(1)
        space_left -= new_height + MARGIN  

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

if __name__ =='__main__':
    st.set_page_config(layout = "wide", 
                       initial_sidebar_state = "auto", 
                       page_title = "Ensayos Aleatorios")
    
    st.header('Ensayos Aleatorios', divider='green')
    st.subheader("_En esta página web_ :blue[podrás crear ensayos aleatorios para preparar tu prueba] :red[PAES M1] :orange[2025] :sunglasses:")

    with st.container(border=True):

        st.header("Selecciona el número de preguntas por eje")
        with st.form("number_of_questions"):
            
            n = st.radio('Seleccionar el número de preguntas', 
                         options = [3, 4, 5], 
                         index = st.session_state.get("n", 0), 
                         label_visibility = "hidden")       
            submit_button_n = st.form_submit_button("Seleccionar")

            if submit_button_n:
                st.session_state["n"] = [3,4,5].index(n)

    with st.container(border=True):

        st.header("Ingresa el número de forma (opcional)")
        with st.form("seed_number"):
            input_seed = st.text_input('Ingresar el número de la semilla (forma) para generar', 
                                       placeholder = "Escribe aquí un número",
                                       value = st.session_state.get("input_seed", ""),
                                       label_visibility = "hidden"
            )

            submit_button_seed = st.form_submit_button("Seleccionar")
            if submit_button_seed:
                if input_seed.isdigit() == False or len(input_seed)!=6:
                    st.error("El número seleccionado no es válido")
                else:
                    st.session_state["input_seed"] = input_seed

    with st.container(border=True):

        st.header("Generar pdf")
        with st.form("get_pdf"):
            submit_button_get_pdf = st.form_submit_button("Obtener pdf")    

        if submit_button_get_pdf:
            if input_seed.isdigit() == False or len(input_seed)!=6:
                random_elements_per_category, categories_list, seed = get_random_elements('./database', n)
                layout_pages = get_final_layout(random_elements_per_category, seed)
                pdf_buffer = create_pdf(layout_pages, categories_list, seed)
  

            else:
                random_elements_per_category, categories_list, seed = get_random_elements('./database', n, input_seed)
                layout_pages = get_final_layout(random_elements_per_category, seed)
                pdf_buffer = create_pdf(layout_pages, categories_list, seed)    

            st.session_state["seed"] = seed 
            st.session_state["pdf_buffer"] = pdf_buffer
        
        if "pdf_buffer" in st.session_state:
            st.success("Se creó un ensayo con la forma: {}. Ahora puedes descargarlo.".format(st.session_state["seed"]))
            st.download_button(
                label = "Descargar ensayo PDF",
                data = st.session_state["pdf_buffer"],
                file_name = "ensayo_{}.pdf".format(st.session_state["seed"]),
                mime = "application/pdf"
            )
