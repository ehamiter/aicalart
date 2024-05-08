let currentDate = new Date();
const baseImageUrl = "https://aicalart.s3.amazonaws.com/images/";
const basePromptUrl = "./prompts.json";

let touchstartX = 0;
let touchendX = 0;
let touchstartY = 0;
let touchendY = 0;
let swipeXThreshold = 100;
let swipeYThreshold = 110;

async function loadPrompts(dateString, orientation) {
  const promptUrl = `https://aicalart.s3.amazonaws.com/prompts/${dateString}-prompt.json`;
  const response = await fetch(promptUrl);
  const promptData = await response.json();

  return {
    bgFile: `url('${baseImageUrl}${dateString}-${orientation}.webp')`,
    text: promptData[orientation],
    holidays: promptData["holidays"]
  };
}


function formatDate(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

async function updateImageTitleAndBackground() {
  const dateString = formatDate(currentDate);
  const orientation = window.matchMedia("(orientation: portrait)").matches ? 'portrait' : 'landscape';

  const utcDate = new Date(dateString + 'T00:00:00Z');
  const localDate = new Date(utcDate.getTime() + (utcDate.getTimezoneOffset() * 60 * 1000));

  try {
    const prompts = await loadPrompts(dateString, orientation);
    if (prompts) {
      document.querySelector('.bg-image').style.backgroundImage = prompts.bgFile;
      document.getElementById('modalDate').textContent = localDate.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
      document.getElementById('modalText').textContent = prompts.text;
      document.getElementById('modalHolidays').textContent = prompts.holidays;
    } else {
      // Handle the case where no prompts are found (e.g., clear the UI elements or display a default message)
    }
  } catch (error) {
    console.error('Fetch failed: ', error);
  }
}

function changeDate(days) {
  let newDate = new Date(currentDate.valueOf());
  newDate.setDate(newDate.getDate() + days);

  // Get today's date in the viewer's local timezone
  let today = new Date();
  today.setHours(23, 59, 59, 999); // Set to the end of today in local timezone

  let firstDate = new Date('2023-11-25T00:00:00-06:00'); // CST timezone offset for the first date

  if (newDate > today) {
    console.error('Cannot navigate to a future date.');
    return;
  }

  if (newDate < firstDate) {
    console.error('Cannot navigate before November 25, 2023.');
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

// Function to handle "Go" button click or enter key press in date input
function jumpToDate() {
  var dateInputElement = document.getElementById("dateInput");
  var datePattern = /^\d{4}-\d{2}-\d{2}$/;
  if (datePattern.test(dateInputElement.value)) {
    window.location.hash = dateInputElement.value;
    currentDate = extractDateFromUrl();
    updateImageTitleAndBackground();
    toggleJumpToDateModal();
    dateInputElement.blur(); // remove focus from the input element itself
  } else {
    alert("Please enter a valid date in YYYY-MM-DD format.");
  }
}

document.getElementById("jumpToDateButton").addEventListener("click", jumpToDate);
document.getElementById("jumpToDateClose").onclick = function() {
  toggleJumpToDateModal();
};

document.getElementById("dateInput").addEventListener("keypress", function(event) {
  if (event.key === "Enter") {
    jumpToDate();
  }
});

function toggleModal(modalId, forceShow) {
  var modal = document.getElementById(modalId);
  console.log('Toggling modal:', modalId, 'Force show:', forceShow);

  // Clear all animations before applying new ones
  modal.classList.remove('modal-show');
  modal.classList.remove('modal-hide');

  if (forceShow === undefined) {
    // Check current visibility to toggle appropriately
    if (modal.classList.contains('modal-visible')) {
      modal.classList.add('modal-hide');
      modal.classList.remove('modal-visible');
    } else {
      modal.classList.add('modal-show');
      modal.classList.add('modal-visible');
      modal.scrollTop = 0;
    }
  } else if (forceShow) {
    modal.classList.add('modal-show');
    modal.classList.add('modal-visible');
    modal.scrollTop = 0;
  } else {
    modal.classList.add('modal-hide');
    modal.classList.remove('modal-visible');
  }
}

function toggleJumpToDateModal() {
  var jumpToDateModal = document.getElementById("jumpToDateModal");

  if (jumpToDateModal.classList.contains('modal-show')) {
    jumpToDateModal.classList.remove('modal-show');
    jumpToDateModal.classList.add('modal-hide');
  } else {
    jumpToDateModal.classList.add('modal-show');
    jumpToDateModal.classList.remove('modal-hide');
  }
}

document.addEventListener('DOMContentLoaded', function() {
  currentDate = extractDateFromUrl();
  updateImageTitleAndBackground();
  const image = document.querySelector('.bg-image');
  image.style.animationPlayState = 'paused';

  document.addEventListener('keydown', function(event) {
    const image = document.querySelector('.bg-image');
    if (event.key === 'j') {
      toggleModal('jumpToDateModal');
    } else if (event.key === 'p') {
      toggleModal('promptModal');
    } else if (event.key === '?') {
      toggleModal('aboutModal');
    } else if (event.key === 'k' || event.key === 'q') {
      // Handle Ken Burns effect, no modal toggling required here
      handleKenBurnsEffect(event.key);
    } else if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
      // Navigate dates, no modal toggling required directly here
      changeDate(event.key === 'ArrowRight' ? 1 : -1);
      }
    });

  function handleKenBurnsEffect(key) {
    if (key === 'k') {
      if (image.style.animationPlayState === 'paused') {
        image.style.animationPlayState = 'running';
        console.log('Ken Burns mode activated!');
      } else {
        image.style.animationPlayState = 'paused';
      }
    } else if (key === 'q') {
      image.style.animation = 'none';
      image.offsetHeight;
      image.style.transform = 'scale(1)';
      image.style.backgroundPosition = '50% 50%';
      image.style.animation = 'kenburns 88s linear infinite';
      image.style.animationPlayState = 'paused';
      console.log('Ken Burns mode deactivated.');
    }
  }
// });


  function handleSwipeGesture() {
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
          toggleModal('promptModal', true);
        } else if (touchendY > touchstartY) {
          toggleModal('promptModal', false);
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
