(function() {
  "use strict";

  var answers = {};
  var totalQuestions = document.querySelectorAll(".question-card").length;
  var allCards = document.querySelectorAll(".question-card");
  var allBtns = document.querySelectorAll(".option-btn");
  var submitArea = document.getElementById("submitArea");
  var submitBtn = document.getElementById("submitBtn");
  var progressFill = document.getElementById("progressFill");
  var progressText = document.getElementById("progressText");
  var resultsDiv = document.getElementById("results");
  var loading = document.getElementById("loading");

  var drugComments = {
    "Cannabis": "The perennial favourite. It's been number one since records began in 1995.",
    "Powder cocaine": "Friday night's open secret \u2014 popularity peaks in the 25\u201329 bracket.",
    "Ecstasy": "Still going strong three decades after the Second Summer of Love.",
    "Hallucinogens": "Magic mushrooms and LSD \u2014 nature and chemistry's mind-benders.",
    "Ketamine": "From veterinary anaesthetic to nightlife staple in a single generation.",
    "Amphetamines": "Speed: quietly persistent since the Northern Soul all-nighters."
  };

  // Reveal cards with staggered animation
  function revealCards() {
    allCards.forEach(function(card, i) {
      setTimeout(function() {
        card.classList.add("visible");
      }, 80 * i);
    });
  }

  function updateProgress() {
    var count = Object.keys(answers).length;
    var pct = Math.round((count / totalQuestions) * 100);
    progressFill.style.width = pct + "%";
    progressText.textContent = count + " / " + totalQuestions;
    if (count >= 3) {
      submitArea.classList.add("ready");
      submitBtn.disabled = false;
    }
  }

  // Handle option selection
  function handleOptionClick(e) {
    var btn = e.target;
    if (!btn.classList.contains("option-btn")) return;

    var qid = btn.getAttribute("data-qid");
    var value = btn.getAttribute("data-value");

    // Deselect siblings
    var siblings = btn.parentNode.querySelectorAll(".option-btn");
    siblings.forEach(function(s) { s.classList.remove("selected"); });

    // Select this one
    btn.classList.add("selected");
    answers[qid] = value;

    // Dim the answered card after a beat
    var card = document.getElementById("card-" + qid);
    setTimeout(function() {
      card.classList.add("answered");
    }, 300);

    updateProgress();
  }

  // Allow clicking answered card to re-expand it
  allCards.forEach(function(card) {
    card.addEventListener("click", function(e) {
      if (card.classList.contains("answered") && !e.target.classList.contains("option-btn")) {
        card.classList.remove("answered");
      }
    });
  });

  document.getElementById("questionnaire").addEventListener("click", handleOptionClick);

  // Submit
  submitBtn.addEventListener("click", function() {
    document.getElementById("questionnaire").style.display = "none";
    submitArea.style.display = "none";
    loading.classList.add("show");

    fetch("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(answers)
    })
    .then(function(res) { return res.json(); })
    .then(function(data) { renderResults(data); })
    .catch(function(err) {
      loading.classList.remove("show");
      alert("Something went wrong. Please try again.");
      console.error(err);
    });
  });

  function renderResults(drugs) {
    loading.classList.remove("show");

    // Compute a rough "any drug" estimate from top rates
    var topThreeSum = drugs.slice(0, 3).reduce(function(s, d) { return s + d.rate; }, 0);
    // Inclusion-exclusion rough approximation
    var anyDrug = Math.min(topThreeSum * 0.85, 95);

    var verdict;
    if (anyDrug > 20) verdict = "The government is fairly confident you\u2019re partying.";
    else if (anyDrug > 12) verdict = "A statistical side-eye from Whitehall.";
    else if (anyDrug > 7) verdict = "Statistically average \u2014 you blend into the crowd.";
    else if (anyDrug > 3) verdict = "Statistically squeaky-clean, but not implausibly so.";
    else verdict = "The Home Office considers you an absolute saint.";

    var maxRate = drugs[0].rate;

    var html = '<div class="results-header">';
    html += '<h2>Your Government Drug Profile</h2>';
    html += '<p class="verdict">' + verdict + '</p>';
    html += '</div>';

    html += '<div class="any-drug-stat">';
    html += '<div class="any-drug-pct">' + anyDrug.toFixed(1) + '%</div>';
    html += '<div class="any-drug-label">estimated chance you\'ve used any illegal drug in the past year</div>';
    html += '</div>';

    html += '<div class="drug-list">';
    drugs.forEach(function(d, i) {
      var classSlug = d.classification.toLowerCase().replace(/\s+/g, "-");
      var barClass = classSlug || "default";
      var barWidth = maxRate > 0 ? Math.max((d.rate / maxRate) * 100, 0.5) : 0;
      var comment = drugComments[d.drug] || "";
      var rankClass = i < 3 ? "top" : "";

      html += '<div class="drug-row">';
      html += '<div class="drug-rank ' + rankClass + '">' + (i + 1) + '</div>';
      html += '<div class="drug-info">';
      html += '<span class="drug-name">' + d.drug + '</span>';
      if (d.classification) {
        html += '<span class="drug-class ' + barClass + '">' + d.classification + '</span>';
      }
      html += '<div class="drug-bar-wrap">';
      html += '<div class="drug-bar"><div class="drug-bar-fill ' + barClass + '" data-width="' + barWidth + '"></div></div>';
      html += '</div>';
      if (comment) {
        html += '<div class="drug-comment">' + comment + '</div>';
      }
      html += '</div>';
      html += '<div class="drug-pct">' + d.rate.toFixed(2) + '%</div>';
      html += '</div>';
    });
    html += '</div>';

    html += '<div class="disclaimer">';
    html += '<strong>Disclaimer.</strong> ';
    html += 'This is a statistical toy based on published survey data from the Crime Survey for England and Wales (year ending March 2025). ';
    html += 'Rates are adjusted using a geometric mean of demographic-specific prevalences \u2014 a simplification of complex, correlated factors. ';
    html += 'The figures shown are not a prediction of <em>your</em> actual behaviour, nor should they be taken as advice or accusation. ';
    html += 'Drug use carries serious health and legal risks. ';
    html += 'No personal data is stored or transmitted beyond this page.';
    html += '</div>';

    html += '<button type="button" class="restart-btn" onclick="location.reload()">Start Again</button>';

    resultsDiv.innerHTML = html;
    resultsDiv.classList.add("show");

    // Animate bars after a tick
    setTimeout(function() {
      var fills = resultsDiv.querySelectorAll(".drug-bar-fill");
      fills.forEach(function(f) {
        f.style.width = f.getAttribute("data-width") + "%";
      });
    }, 100);

    // Scroll to results
    resultsDiv.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  // Init
  revealCards();

})();
