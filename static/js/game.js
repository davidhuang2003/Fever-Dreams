(() => {
  "use strict";

  const root = document.querySelector("#game-root");
  if (!root) return;

  const choiceList = document.querySelector("#choice-list");
  const message = document.querySelector("#game-message");
  let requestPending = false;

  function setPending(pending) {
    requestPending = pending;
    choiceList.querySelectorAll("button").forEach((button) => {
      button.disabled = pending;
    });
  }

  function updateScore(name, value) {
    const progress = document.querySelector(`#${name}-score`);
    if (progress) {
      progress.value = value;
      progress.textContent = String(value);
    }
  }

  function renderChoices(choices) {
    choiceList.replaceChildren();

    choices.forEach((choice) => {
      const button = document.createElement("button");
      button.className = "choice-card";
      button.type = "button";
      button.dataset.choiceId = choice.id;

      const label = document.createElement("strong");
      label.textContent = choice.choice_text;

      const cost = document.createElement("span");
      cost.textContent = `${choice.time_cost} hr · $${choice.budget_cost}`;

      button.append(label, cost);
      choiceList.append(button);
    });
  }

  function renderState(state) {
    document.querySelector("#budget-value").textContent = `$${state.remaining_budget}`;
    document.querySelector("#time-value").textContent = `${state.remaining_time} hours`;
    document.querySelector("#phase-label").textContent = state.current_point.phase;
    document.querySelector("#position-value").textContent = state.current_point.position;
    document.querySelector("#decision-prompt").textContent = state.current_point.prompt;

    updateScore("supplies", state.scores.supplies);
    updateScore("communication", state.scores.communication);
    updateScore("safety", state.scores.safety);
    updateScore("community", state.scores.community);
    renderChoices(state.choices);

    window.dispatchEvent(new CustomEvent("fever-dreams:state", { detail: state }));
  }

  async function submitChoice(choiceId) {
    if (requestPending) return;

    setPending(true);
    message.textContent = "Applying your choice…";

    try {
      const response = await fetch(root.dataset.choiceUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ choice_id: Number(choiceId) }),
      });

      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.error || "That choice could not be recorded.");
      }

      if (payload.status === "completed" && payload.results_url) {
        window.location.assign(payload.results_url);
        return;
      }

      renderState(payload);
      message.textContent = payload.feedback || "Choice recorded.";
    } catch (error) {
      message.textContent = error.message;
    } finally {
      setPending(false);
    }
  }

  choiceList.addEventListener("click", (event) => {
    const button = event.target.closest("[data-choice-id]");
    if (button) submitChoice(button.dataset.choiceId);
  });
})();

