// Constants
let currentDate = new Date();
const baseImageUrl = "https://aicalart.s3.amazonaws.com/images/";
const swipeXThreshold = 100;
const swipeYThreshold = 110;

// Date and URL functions
function formatDate(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

function formatToLongDate(date) {
  const options = { year: 'numeric', month: 'long', day: 'numeric' };
  return date.toLocaleDateString('en-US', options);
}

function extractDateFromUrl() {
  const hash = window.location.hash;
  const datePattern = /^#(\d{4}-\d{2}-\d{2})$/;
  const match = hash.match(datePattern);
  if (!match) return;

  const [year, month, day] = match[1].split('-').map(num => parseInt(num, 10));
  currentDate = new Date(year, month - 1, day);
}

async function loadPrompts(dateString, orientation) {
  const promptUrl = `https://aicalart.s3.amazonaws.com/prompts/${dateString}-prompt.json`;
  try {
    const response = await fetch(promptUrl);
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    const promptData = await response.json();
    return {
      bgFile: `url('${baseImageUrl}${dateString}-${orientation}.webp')`,
      text: promptData[orientation],
      holidays: promptData["holidays"],
      style: promptData["style"] || ''
    };
  } catch (error) {
    console.error("Error fetching or parsing data:", error);
    return null;
  }
}

async function updateImageTitleAndBackground() {
  const dateString = formatDate(currentDate);
  const orientation = window.matchMedia("(orientation: portrait)").matches ? 'portrait' : 'landscape';

  try {
    const prompts = await loadPrompts(dateString, orientation);
    if (!prompts) return;

    document.querySelector('.bg-image').style.backgroundImage = prompts.bgFile;
    document.getElementById('modalDate').textContent = formatToLongDate(currentDate);;
    document.getElementById('modalText').textContent = prompts.text;
    document.getElementById('modalHolidays').textContent = prompts.holidays;
    document.getElementById('modalStyle').textContent = prompts.style || '';
  } catch (error) {
    console.error('Fetch failed: ', error);
  }
}

// Date navigation functions
function changeDate(days) {
  const newDate = new Date(currentDate.getTime());
  newDate.setDate(newDate.getDate() + days);
  const today = new Date();
  today.setHours(23, 59, 59, 999);

  if (newDate > today || newDate < new Date('2023-11-25T00:00:00-06:00')) {
    console.error('Date navigation out of bounds.');
    return;
  }

  currentDate = newDate;
  updateImageTitleAndBackground();
}

// Modal handling functions
function toggleModal(modalId, forceShow) {
  const modal = document.getElementById(modalId);
  if (!modal) {
    console.error("Modal not found: ", modalId);
    return;
  }

  // Remove any existing event listeners to prevent duplicates
  modal.removeEventListener('animationend', onAnimationEnd);

  // Determine current visibility to toggle or use the provided forceShow value
  const isVisible = modal.classList.contains('modal-visible');
  forceShow = forceShow !== undefined ? forceShow : !isVisible;

  // Prepare the modal by clearing any previously set animations
  modal.style.animation = 'none';
  modal.offsetHeight; // Trigger reflow

  function onAnimationEnd() {
    // Only update visibility when hiding
    if (!forceShow) {
      modal.classList.remove('modal-visible');
    }
    modal.removeEventListener('animationend', onAnimationEnd);
  }

  if (forceShow) {
    modal.classList.add('modal-show', 'modal-visible');
    modal.classList.remove('modal-hide');
  } else {
    modal.classList.add('modal-hide');
    modal.classList.remove('modal-show');
    // Listen for the end of the hide animation to remove visibility
    modal.addEventListener('animationend', onAnimationEnd);
  }

  // Reapply animation after setup
  modal.style.animation = '';
}

// Clipboard function
function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => {
    console.log('Copied URL to clipboard: ', text);
  }).catch(err => {
    console.error('Failed to copy text: ', err);
  });
}

// Initialization and event bindings
document.addEventListener('DOMContentLoaded', () => {
  extractDateFromUrl();
  updateImageTitleAndBackground();
  document.querySelector('.bg-image').style.animationPlayState = 'paused';

  document.addEventListener('keydown', handleKeyPress);
  document.addEventListener('touchstart', handleTouchStart);
  document.addEventListener('touchend', handleSwipeGesture);
  window.addEventListener("resize", updateImageTitleAndBackground);
});

function handleKeyPress(event) {
  const modalMap = { 'p': 'promptModal', '?' : 'aboutModal' };
  if (modalMap[event.key]) {
    // Toggle the modal based on its current visibility
    const modal = document.getElementById(modalMap[event.key]);
    const isModalVisible = modal.classList.contains('modal-visible');
    toggleModal(modalMap[event.key], !isModalVisible);
  } else if (['k', 'q'].includes(event.key)) {
    handleKenBurnsEffect(event.key);
  } else if (['ArrowLeft', 'ArrowRight'].includes(event.key)) {
    changeDate(event.key === 'ArrowRight' ? 1 : -1);
  } else if (event.key === 'c') {
    const dateString = formatDate(currentDate);
    const orientation = window.matchMedia("(orientation: portrait)").matches ? 'portrait' : 'landscape';
    const imageUrl = `${baseImageUrl}${dateString}-${orientation}.webp`;
    copyToClipboard(imageUrl);
  }
}

function handleKenBurnsEffect(key) {
  const image = document.querySelector('.bg-image');
  const isPaused = image.style.animationPlayState === 'paused';
  if (key === 'k') image.style.animationPlayState = isPaused ? 'running' : 'paused';
  else resetKenBurnsEffect(image);
}

function resetKenBurnsEffect(image) {
  image.style.animation = 'none';
  image.offsetHeight; // Trigger reflow
  image.style.transform = 'scale(1)';
  image.style.backgroundPosition = '50% 50%';
  image.style.animation = 'kenburns 88s linear infinite';
  image.style.animationPlayState = 'paused';
}

function handleTouchStart(event) {
  if (event.touches.length !== 1) return;
  [touchstartX, touchstartY] = [event.touches[0].screenX, event.touches[0].screenY];
}

function handleSwipeGesture(event) {
  if (event.changedTouches.length !== 1) return;

  const touchendX = event.changedTouches[0].screenX;
  const touchendY = event.changedTouches[0].screenY;

  const swipeXDistance = Math.abs(touchendX - touchstartX);
  const swipeYDistance = Math.abs(touchendY - touchstartY);

  if (swipeYDistance > swipeXDistance && swipeYDistance > swipeYThreshold) {
    toggleModal('promptModal', touchendY < touchstartY);
  } else if (swipeXDistance > swipeYDistance && swipeXDistance > swipeXThreshold) {
    changeDate(touchendX < touchstartX ? 1 : -1);
  }
}
