// Add participant
document.getElementById("add-participant-form").addEventListener("submit", function (event) {
    event.preventDefault();
    const participant = document.getElementById("new-participant").value;

    fetch("/add_participant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ participant })
    }).then(response => response.json())
      .then(data => {
          alert(data.message);
      });
});

// Delete participant
document.getElementById("delete-participant-form").addEventListener("submit", function (event) {
    event.preventDefault();
    const participant = document.getElementById("delete-participant").value;

    fetch("/delete_participant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ participant })
    }).then(response => response.json())
      .then(data => {
          alert(data.message);
      });
});

// Refresh expenses
document.getElementById("refresh-expenses").addEventListener("click", function () {
    fetch("/refresh_expenses", {
        method: "POST"
    }).then(response => response.json())
      .then(data => {
          alert(data.message);
      });
});

// Delete expense
document.getElementById("delete-expense-form").addEventListener("submit", function (event) {
    event.preventDefault();
    const index = parseInt(document.getElementById("delete-expense-index").value);

    fetch("/delete_expense", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ index })
    }).then(response => response.json())
      .then(data => {
          alert(data.message);
      });
});

// Fetch and display participants
function updateParticipantsList() {
    fetch("/get_participants")
        .then(response => response.json())
        .then(data => {
            const participantsList = document.getElementById("participants-list");
            participantsList.innerHTML = ""; // 清空列表

            // 動態新增參與者到列表
            data.participants.forEach(participant => {
                const listItem = document.createElement("li");
                listItem.textContent = participant;
                participantsList.appendChild(listItem);
            });
        });
}

// 在頁面加載時載入參與者列表
document.addEventListener("DOMContentLoaded", function () {
    updateParticipantsList();
});

// 在新增或刪除參與者後更新列表
document.getElementById("add-participant-form").addEventListener("submit", function (event) {
    event.preventDefault();
    const participant = document.getElementById("new-participant").value;

    fetch("/add_participant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ participant })
    }).then(response => response.json())
      .then(data => {
          alert(data.message);
          updateParticipantsList(); // 更新列表
      });
});

document.getElementById("delete-participant-form").addEventListener("submit", function (event) {
    event.preventDefault();
    const participant = document.getElementById("delete-participant").value;

    fetch("/delete_participant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ participant })
    }).then(response => response.json())
      .then(data => {
          alert(data.message);
          updateParticipantsList(); // 更新列表
      });
});
