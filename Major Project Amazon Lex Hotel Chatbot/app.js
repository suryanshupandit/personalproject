const ROOM_CATALOG = {
  Classic: {
    price: 1500,
    description: "Comfortable standard room for a budget-friendly stay."
  },
  Duplex: {
    price: 3000,
    description: "Two-level room with extra space for families or groups."
  },
  Suite: {
    price: 5000,
    description: "Premium room with enhanced comfort and amenities."
  },
  Deluxe: {
    price: 4000,
    description: "Spacious upgraded room with modern facilities."
  },
  Family: {
    price: 4500,
    description: "Designed for family stays with extra bedding space."
  },
  Executive: {
    price: 6000,
    description: "Executive-class stay for business and premium guests."
  }
};

const state = {
  roomType: null,
  nights: null,
  checkInDate: null,
  step: "room"
};

const chatWindow = document.getElementById("chatWindow");
const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const quickActions = document.getElementById("quickActions");
const roomCatalog = document.getElementById("roomCatalog");
const restartBtn = document.getElementById("restartBtn");

function formatCurrency(value) {
  return `Rs. ${value}`;
}

function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = `message ${role}`;
  div.textContent = text;
  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function setQuickActions(actions) {
  quickActions.innerHTML = "";
  actions.forEach((label) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "chip";
    btn.textContent = label;
    btn.addEventListener("click", () => {
      chatInput.value = label;
      chatForm.requestSubmit();
    });
    quickActions.appendChild(btn);
  });
}

function showRoomCatalog() {
  roomCatalog.innerHTML = "";
  Object.entries(ROOM_CATALOG).forEach(([name, data]) => {
    const card = document.createElement("article");
    card.className = "room-card";
    card.innerHTML = `
      <h3>${name}</h3>
      <p>${data.description}</p>
      <div class="price">${formatCurrency(data.price)} / night</div>
    `;
    roomCatalog.appendChild(card);
  });
}

function normalizeRoomType(input) {
  const typed = input.trim().toLowerCase();
  return Object.keys(ROOM_CATALOG).find((room) => room.toLowerCase() === typed) || null;
}

function isValidDate(input) {
  const date = new Date(input);
  if (Number.isNaN(date.getTime())) {
    return false;
  }

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return date >= today;
}

function promptCurrentStep() {
  if (state.step === "room") {
    addMessage("bot", "Choose your room type: Classic, Duplex, Suite, Deluxe, Family, or Executive.");
    setQuickActions(Object.keys(ROOM_CATALOG));
    chatInput.placeholder = "Example: Duplex";
  } else if (state.step === "nights") {
    addMessage("bot", "How many nights would you like to stay? (1 to 30)");
    setQuickActions(["1", "2", "3", "5", "7"]);
    chatInput.placeholder = "Example: 3";
  } else if (state.step === "checkInDate") {
    addMessage("bot", "What is your check-in date? Use YYYY-MM-DD format.");
    setQuickActions([]);
    chatInput.placeholder = "Example: 2026-05-20";
  }
}

function bookingSummary() {
  const room = state.roomType;
  const nights = state.nights;
  const checkInDate = state.checkInDate;
  const nightly = ROOM_CATALOG[room].price;
  const total = nightly * nights;

  return `Booking confirmed. Your ${room} room is reserved from ${checkInDate} for ${nights} day(s). Price per night is ${formatCurrency(nightly)}, so total cost is ${formatCurrency(total)}.`;
}

async function submitBookingToBackend() {
  const payload = {
    roomType: state.roomType,
    nights: state.nights,
    checkInDate: state.checkInDate
  };

  const response = await fetch("/api/book", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  const data = await response.json();
  if (!response.ok || !data.ok) {
    throw new Error(data.message || "Booking API request failed.");
  }

  return data.message;
}

function restartFlow() {
  state.roomType = null;
  state.nights = null;
  state.checkInDate = null;
  state.step = "room";

  chatWindow.innerHTML = "";
  addMessage("bot", "Welcome to the BookHotel Assistant.");
  promptCurrentStep();
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = chatInput.value.trim();
  if (!text) {
    return;
  }

  addMessage("user", text);

  if (state.step === "room") {
    const selectedRoom = normalizeRoomType(text);
    if (!selectedRoom) {
      addMessage("bot", "Invalid room type. Please pick one of the available categories.");
      setQuickActions(Object.keys(ROOM_CATALOG));
      chatInput.value = "";
      return;
    }

    state.roomType = selectedRoom;
    state.step = "nights";
    addMessage("bot", `${selectedRoom} selected at ${formatCurrency(ROOM_CATALOG[selectedRoom].price)} per night.`);
    promptCurrentStep();
  } else if (state.step === "nights") {
    const nights = Number.parseInt(text, 10);
    if (Number.isNaN(nights) || nights < 1 || nights > 30) {
      addMessage("bot", "Please enter a valid number from 1 to 30.");
      setQuickActions(["1", "2", "3", "5", "7"]);
      chatInput.value = "";
      return;
    }

    state.nights = nights;
    state.step = "checkInDate";
    promptCurrentStep();
  } else if (state.step === "checkInDate") {
    if (!isValidDate(text)) {
      addMessage("bot", "Please enter a valid current or future date in YYYY-MM-DD format.");
      chatInput.value = "";
      return;
    }

    state.checkInDate = text;
    state.step = "complete";
    setQuickActions(["Restart Booking"]);

    try {
      const backendSummary = await submitBookingToBackend();
      addMessage("bot", backendSummary);
    } catch (error) {
      const fallbackSummary = `${bookingSummary()} Thank you for choosing our hotel.`;
      addMessage("bot", `${fallbackSummary}\n(Backend not reachable, showing local summary.)`);
      addMessage("bot", `Error: ${error.message}`);
    }

    addMessage("bot", "Type Restart Booking or click Restart to create a new booking.");
  } else if (state.step === "complete") {
    if (text.toLowerCase() === "restart booking" || text.toLowerCase() === "restart") {
      restartFlow();
    } else {
      addMessage("bot", "Booking already completed. Type Restart Booking to start again.");
      setQuickActions(["Restart Booking"]);
    }
  }

  chatInput.value = "";
});

restartBtn.addEventListener("click", restartFlow);

showRoomCatalog();
restartFlow();
