
window.addEventListener('scroll', function () {// navbar kaydırılınca renk değiştiriyor
  const navbar = document.querySelector('.gizlinavbar');
  if (window.scrollY > 50) {
    navbar.classList.add('scrolled');
  } else {
    navbar.classList.remove('scrolled');
  }
});

//kayan ürün menüsünün fonksiyonları
const track = document.querySelector('.slider-track');
const slides = document.querySelectorAll('.slide');
const leftBtn = document.querySelector('.left-btn');
const rightBtn = document.querySelector('.right-btn');

track.style.width = `${(slides.length * 25)}%`; 

let currentIndex = 0;
const totalSlides = slides.length / 2; // Çünkü ürünler iki kere yazıldı.
let autoSlide = setInterval(() => {
  rightBtn.click();
}, 3000); // 3 saniyede bir kay

function startAutoSlide() {
  autoSlide = setInterval(() => {
    rightBtn.click();
  }, 3000);
}

function stopAutoSlide() {
  clearInterval(autoSlide);
} 

function moveNext() {
  index++;
  track.style.transform = `translateX(-${index * slideWidth}px)`;

  if (index >= slides.length / 2) {
    setTimeout(() => {
      track.style.transition = 'none';
      index = 0;
      track.style.transform = `translateX(0px)`;
      setTimeout(() => {
        track.style.transition = 'transform 0.5s ease';
      }, 50);
    }, 500);
  }
}

function updateSlidePosition() {
  track.style.transition = 'transform 0.8s cubic-bezier(0.25, 1, 0.5, 1)';//kayma özelliği burdan değiştiriliyo
  track.style.transform = `translateX(-${currentIndex * 25}%)`;
}

rightBtn.addEventListener('click', () => {
  if (currentIndex >= totalSlides) {
    track.style.transition = 'none';
    currentIndex = 0;
    track.style.transform = `translateX(-${currentIndex * 25}%)`;
    setTimeout(() => {
      currentIndex++;
      updateSlidePosition();
    }, 20);
  } else {
    currentIndex++;
    updateSlidePosition();
  }
});

leftBtn.addEventListener('click', () => {
  if (currentIndex <= 0) {
    track.style.transition = 'none';
    currentIndex = totalSlides;
    track.style.transform = `translateX(-${currentIndex * 25}%)`;
    setTimeout(() => {
      currentIndex--;
      updateSlidePosition();
    }, 20);
  } else {
    currentIndex--;
    updateSlidePosition();
  }
});

// Mouse ile slidera gelince kaydırmayı durdur
const sliderContainer = document.querySelector('.slider-container');
sliderContainer.addEventListener('mouseenter', stopAutoSlide);
sliderContainer.addEventListener('mouseleave', startAutoSlide);

document.getElementById('dahaFazlaBtn').addEventListener('click', function() {
  var gizliBasliklar = document.getElementById('dahaFazlaBaslik');
  if (gizliBasliklar.style.display === 'none') {
    gizliBasliklar.style.display = 'block';
    this.textContent = 'Daha Az Göster';
  } else {
    gizliBasliklar.style.display = 'none';
    this.textContent = 'Daha Fazla Göster';
  }
});


//forum kısmının kodları bunun için dediğim gibi karışıklık olmasın diye forum.js açmadım şuan
const banner = document.getElementById('banner');
let ticking = false;

function updateBanner() {
  const scrollY = window.scrollY;

  let height = 300 - scrollY;
  if (height < 80) height = 80;
  if (height > 300) height = 300;

  banner.style.height = `${height}px`;
  ticking = false;
}

window.addEventListener('scroll', () => {
  if (!ticking) {
    window.requestAnimationFrame(updateBanner);
    ticking = true;
  }
});

function togglePassword(id) {
  const input = document.getElementById(id);
  if (input.type === "password") {
    input.type = "text";
  } else {
    input.type = "password";
  }
}