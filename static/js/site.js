let currentDate = new Date();

function formatDate(date) {
  return date.getFullYear() + '-' +
         ('0' + (date.getMonth() + 1)).slice(-2) + '-' +
         ('0' + date.getDate()).slice(-2);
}

function updateImageTitleAndBackground() {
  let dateString = formatDate(currentDate);
  let orientation = window.matchMedia("(orientation: portrait)").matches ? 'portrait' : 'landscape';
  let basePromptUrl = `https://aicalart.s3.amazonaws.com/prompts/`;
  let baseImageUrl = `https://aicalart.s3.amazonaws.com/images/`;

  // Always use dated files
  let textFile = `${basePromptUrl}${dateString}-${orientation}.txt`;
  let bgFile = `url('${baseImageUrl}${dateString}-${orientation}.webp')`;

  fetch(textFile)
  .then(response => response.text())
  .then(text => {
    document.querySelector('.bg-image').setAttribute('title', text);
    document.querySelector('.bg-image').style.backgroundImage = bgFile;
    document.getElementById('modalText').textContent = text;
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
    console.log('Cannot navigate before November 25, 2023');
    return;
  }

  currentDate = newDate;
  updateImageTitleAndBackground();
}


let numberOfClicks = 0;

function secondsResetClick(seconds) {
  setTimeout(function() {
    numberOfClicks = 0;
  }, seconds * 1000);
}

function incrementClicks() {
  numberOfClicks += 1;
  if (numberOfClicks === 3) {
    numberOfClicks = 0;
    toggleModal();
  } else if (numberOfClicks == 2) {
    secondsResetClick(0.75);
  }
}

document.addEventListener('click', incrementClicks);

let touchstartX = 0;
let touchendX = 0;
let swipeThreshold = 50;

function handleSwipeGesture() {
  let swipeXDistance = Math.abs(touchendX - touchstartX);
  if (swipeXDistance > swipeThreshold) {
    if (touchendX < touchstartX) changeDate(1);
    if (touchendX > touchstartX) changeDate(-1);
  }
}

function toggleModal() {
  var modal = document.getElementById("promptModal");
  var isModalDisplayed = window.getComputedStyle(modal).display !== 'none';
  modal.style.display = isModalDisplayed ? 'none' : 'block';
}

function showModal() {
  var modal = document.getElementById("promptModal");
  modal.style.display = 'block';
}

function hideModal() {
  var modal = document.getElementById("promptModal");
  modal.style.display = 'none';
}

document.addEventListener('touchstart', function(event) {
  touchstartX = event.changedTouches[0].screenX;
  touchstartY = event.changedTouches[0].screenY;
});

document.addEventListener('touchend', function(event) {
  touchendX = event.changedTouches[0].screenX;
  touchendY = event.changedTouches[0].screenY;
  handleSwipeGesture();
  incrementClicks();
});

document.addEventListener('keydown', function(event) {
  if (event.key === 'ArrowLeft') {
    changeDate(-1);
  } else if (event.key === 'ArrowRight') {
    changeDate(1);
  } else if (event.key === '?') {
    toggleModal();
  }
});

window.addEventListener("resize", updateImageTitleAndBackground);
window.onload = updateImageTitleAndBackground;

var closeButton = document.querySelector(".close");
closeButton.onclick = function() {
  var modal = document.getElementById("promptModal");
  modal.style.display = "none";
}

window.onclick = function(event) {
  var modal = document.getElementById("promptModal");
  if (event.target === modal) {
    modal.style.display = "none";
  }
}
