
const carousel = document.getElementById('carouselExampleInterval');

// Carousel kaydırıldığında tetiklenen event
carousel.addEventListener('slide.bs.carousel', function (event) {
  const index = event.to; // Aktivite edilen slide'ın index değeri

});
carousel.addEventListener('slide.bs.carousel', function (event) {
  const items = carousel.querySelectorAll('.carousel-item');
  
  // Tüm resimlerin opaklığını sıfırlar(geçici olarak şeffaf yapar)
  items.forEach(item => {
    item.classList.remove('fade');
    item.style.opacity = 0;
  });

  // Yeni aktive edilen resme fade animasyonunu ekler
  const activeItem = items[event.to];
  activeItem.classList.add('fade');
  activeItem.style.opacity = 1;
});