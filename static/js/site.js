let currentDate = new Date();
let touchstartX = 0;
let touchendX = 0;
let touchstartY = 0;
let touchendY = 0;
let swipeXThreshold = 100;
let swipeYThreshold = 110;

function formatDate(date) {
  return date.getFullYear() + '-' +
         ('0' + (date.getMonth() + 1)).slice(-2) + '-' +
         ('0' + date.getDate()).slice(-2);
}

function convertDateStringToLocaleDateString(dateString) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    const date = new Date(dateString + 'T00:00');
    return date.toLocaleDateString('en-US', options);
}

function updateImageTitleAndBackground() {
  let dateString = formatDate(currentDate);
  let localeDateString = convertDateStringToLocaleDateString(dateString);
  let orientation = window.matchMedia("(orientation: portrait)").matches ? 'portrait' : 'landscape';
  let basePromptUrl = `https://aicalart.s3.amazonaws.com/prompts/`;
  let baseImageUrl = `https://aicalart.s3.amazonaws.com/images/`;

  // Always use dated files
  let bgFile = `url('${baseImageUrl}${dateString}-${orientation}.webp')`;
  let textFile = `${basePromptUrl}${dateString}-${orientation}.txt`;
  let holidayFile = `${basePromptUrl}${dateString}-holidays.txt`;

  fetch(textFile)
    .then(response => response.text())
    .then(text => {
      document.querySelector('.bg-image').style.backgroundImage = bgFile;
      document.getElementById('modalDate').textContent = localeDateString;
      document.getElementById('modalText').textContent = text;

      // Fetch the holiday data
      return fetch(holidayFile);
    })
    .then(response => response.text())
    .then(holidays => {
      document.getElementById('modalHolidays').textContent = holidays;
    })
    .catch(error => {
      console.error('Fetch failed: ', error);
    });
}

function changeDate(days) {
  let newDate = new Date(currentDate.valueOf());
  newDate.setDate(newDate.getDate() + days);

  let today = new Date();
  today.setHours(0, 0, 0, 0);

  let todayStripped = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  let newDateStripped = new Date(newDate.getFullYear(), newDate.getMonth(), newDate.getDate());

  // Only prevent navigating to future dates
  if (newDateStripped > todayStripped) {
    console.log('Cannot navigate to a future date.');
    return;
  }

  let minDate = new Date('2023-11-25');
  if (newDateStripped < minDate) {
    console.log('Cannot navigate before November 25, 2023.');
    return;
  }

  currentDate = newDate;
  updateImageTitleAndBackground();
}

function extractDateFromUrl() {
    const hash = window.location.hash;
    const datePattern = /^#(\d{4}-\d{2}-\d{2})$/;
    const match = hash.match(datePattern);
    if (match) {
      const dateParts = match[1].split('-');
      const year = parseInt(dateParts[0], 10);
      const month = parseInt(dateParts[1], 10);
      const day = parseInt(dateParts[2], 10);

      let date = new Date(year, month - 1, day);
      let formattedDate = date.getFullYear() + '-' +
          ('0' + (date.getMonth() + 1)).slice(-2) + '-' +
          ('0' + date.getDate()).slice(-2);

      console.log('Traveling in time to ' + formattedDate);
      currentDate = new Date(date.toLocaleString('en-US', { timeZone: 'America/Chicago' }));
    }

    return currentDate;
}

function toggleModal(forceShow) {
  var modal = document.getElementById("promptModal");
  if (forceShow === undefined) {
    if (modal.classList.contains('modal-show')) {
      modal.classList.remove('modal-show');
      modal.classList.add('modal-hide');
    } else {
      modal.classList.add('modal-show');
      modal.classList.remove('modal-hide');
      modal.scrollTop = 0;
    }
  } else if (forceShow) {
    modal.classList.add('modal-show');
    modal.classList.remove('modal-hide');
    modal.scrollTop = 0;
  } else {
    modal.classList.remove('modal-show');
    modal.classList.add('modal-hide');
  }
}

document.addEventListener('DOMContentLoaded', function() {
  currentDate = extractDateFromUrl();
  updateImageTitleAndBackground();
  const image = document.querySelector('.bg-image');
  image.style.animationPlayState = 'paused';

  document.addEventListener('keydown', function(event) {
    const image = document.querySelector('.bg-image');
    var aboutModal = document.getElementById("aboutModal");
    if (event.key === 'p') {
      toggleModal();
    } else if (event.key === '?') {
      if (aboutModal.classList.contains('modal-show')) {
        aboutModal.classList.remove('modal-show');
        aboutModal.classList.add('modal-hide');
      } else {
        aboutModal.classList.add('modal-show');
        aboutModal.classList.remove('modal-hide');
      }
    } else if (event.key === 'k') {
      if (image.style.animationPlayState === 'paused') {
        image.style.animationPlayState = 'running';
        console.log('Secret Ken Burns mode!')
      } else {
        image.style.animationPlayState = 'paused';
      }
    } else if (event.key === 'q') {
      image.style.animation = 'none';
      image.offsetHeight;
      image.style.transform = 'scale(1)';
      image.style.backgroundPosition = '50% 50%';
      image.style.animation = 'kenburns 88s linear infinite';
      image.style.animationPlayState = 'paused';
      console.log('Ken Burns has left the building.')
    } else if (event.key === 'ArrowLeft') {
      changeDate(-1);
    } else if (event.key === 'ArrowRight') {
      changeDate(1);
    }

    var promptModalClose = document.querySelector('#promptModal .close');
    promptModalClose.onclick = function() {
      promptModal.classList.remove('modal-show');
      promptModal.classList.add('modal-hide');
    };

    var aboutModalClose = document.querySelector('#aboutModal .close');
    aboutModalClose.onclick = function() {
      aboutModal.classList.remove('modal-show');
      aboutModal.classList.add('modal-hide');
    };

  });

  function handleSwipeGesture() {
    if (event.touches.length > 1) {
      // Ignore pinch/zoom gestures
      return;
    }

    let swipeXDistance = Math.abs(touchendX - touchstartX);
    if (swipeXDistance > swipeXThreshold) {
      if (touchendX < touchstartX) {
        changeDate(1);
      } else if (touchendX > touchstartX) {
        changeDate(-1);
      }
    }
    let swipeYDistance = Math.abs(touchendY - touchstartY);
    if (swipeYDistance > swipeYThreshold) {
      if (touchendY < touchstartY) {
        toggleModal(true);
      } else if (touchendY > touchstartY) {
        toggleModal(false);
      }
    }
  }

  document.addEventListener('touchstart', function(event) {
    if (event.touches.length === 1) {
      touchstartX = event.touches[0].screenX;
      touchstartY = event.touches[0].screenY;
    }
  });

  document.addEventListener('touchend', function(event) {
    if (event.changedTouches.length === 1) {
      touchendX = event.changedTouches[0].screenX;
      touchendY = event.changedTouches[0].screenY;
      handleSwipeGesture();
    }
  });

  window.addEventListener("resize", updateImageTitleAndBackground);
  window.onload = updateImageTitleAndBackground;

});
