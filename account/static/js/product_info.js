// Küçük görsele tıklanınca büyük resmi ve linki değiştir
  function changeImage(imageSrc) {
    const mainImage = document.getElementById('mainProductImage');
    mainImage.src = imageSrc;
    mainImage.parentElement.href = imageSrc;
  }

  // Yorum formunu açar
  function openCommentForm() {
    document.getElementById('commentForm').style.display = 'block';
    document.getElementById('backdrop').style.display = 'block';
  }

  // Yorum formunu kapatır
  function closeCommentForm() {
    document.getElementById('commentForm').style.display = 'none';
    document.getElementById('backdrop').style.display = 'none';
  }

  // Resme tıklanınca modal içinde açar
  function openImageModal(src) {
    document.getElementById('imageModal').style.display = 'block';
    document.getElementById('modalImage').src = src;
  }

  // Modal resmi kapatır
  function closeImageModal() {
    document.getElementById('imageModal').style.display = 'none';
  }

  // DOM yüklendiğinde "Devamını Oku" düğmeleri için toggle işlemi eklenir
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.read-more-btn').forEach(btn => {
      btn.addEventListener('click', function () {
        const comment = btn.previousElementSibling; // .comment-text
        const isExpanded = comment.classList.toggle('expanded');
        btn.textContent = isExpanded ? 'Daha Az Göster' : 'Devamını Oku';
      });
    });
  });

    // Derecelendirme yıldızları için olay dinleyicisi
    document.addEventListener('DOMContentLoaded', function () {
  const stars = document.querySelectorAll('.star-rating .star');
  const ratingInput = document.getElementById('ratingInput');
  let selectedRating = 0;

  stars.forEach((star, index) => {
    star.addEventListener('click', () => {
      selectedRating = index + 1;
      ratingInput.value = selectedRating;
      updateStars();
    });

    star.addEventListener('mouseover', () => {
      highlightStars(index);
    });

    star.addEventListener('mouseout', () => {
      updateStars();
    });
  });

  function updateStars() {
    stars.forEach((star, idx) => {
      star.classList.toggle('selected', idx < selectedRating);
    });
  }

  function highlightStars(index) {
    stars.forEach((star, idx) => {
      star.classList.toggle('hover', idx <= index);
    });
  }
});
