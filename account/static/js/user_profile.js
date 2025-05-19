document.addEventListener('DOMContentLoaded', () => {
  // Sekmeli menü sistemi
  const menuItems = document.querySelectorAll('.menu-item');
  const contents = document.querySelectorAll('.content');

  menuItems.forEach(button => {
    button.addEventListener('click', () => {
      menuItems.forEach(btn => btn.classList.remove('active'));
      button.classList.add('active');
      contents.forEach(section => section.classList.remove('active'));

      const target = button.getAttribute('data-target');
      const activeContent = document.getElementById(target);
      if (activeContent) {
        activeContent.classList.add('active');
      }
    });
  });
});

document.addEventListener("DOMContentLoaded", () => {
  const avatarRadios = document.querySelectorAll('input[name="avatar"]');
  const avatarImages = document.querySelectorAll('.avatar-img');

  avatarRadios.forEach((radio, index) => {
    radio.addEventListener('change', () => {
      avatarImages.forEach(img => img.classList.remove('selected'));
      avatarImages[index].classList.add('selected');
    });
  });
});