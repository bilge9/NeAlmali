let imageIndex = 1;

function addImageField() {
    const container = document.getElementById('image-container');

    const wrapper = document.createElement('div');
    wrapper.classList.add('image-group');

    const input = document.createElement('input');
    input.type = 'file';
    input.name = 'images[]';  // dizi olarak gönder

    const label = document.createElement('label');
    const radio = document.createElement('input');
    radio.type = 'radio';
    radio.name = 'main_image_index';
    radio.value = imageIndex;
    label.appendChild(radio);
    label.appendChild(document.createTextNode(' Ana görsel'));

    wrapper.appendChild(input);
    wrapper.appendChild(label);
    container.appendChild(wrapper);

    imageIndex++;
}

function addAttributeField() {
    const container = document.getElementById('attribute-container');

    const nameInput = document.createElement('input');
    nameInput.type = 'text';
    nameInput.name = 'attributes_name[]';  // dizi olarak gönder
    nameInput.placeholder = 'Özellik Adı';

    const valueInput = document.createElement('input');
    valueInput.type = 'text';
    valueInput.name = 'attributes_value[]';  // dizi olarak gönder
    valueInput.placeholder = 'Özellik Değeri';

    container.appendChild(nameInput);
    container.appendChild(valueInput);
}

function toggleForm() {
    const form = document.getElementById('add-product-form');
    form.classList.toggle('open');
}