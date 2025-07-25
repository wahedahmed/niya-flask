document.addEventListener('DOMContentLoaded', function () {
  document.body.addEventListener('click', function (e) {
    if (e.target.classList.contains('like') || (e.target.closest('.like'))) {
      let btn = e.target.closest('.like');
      let id = btn.getAttribute('data-id');
      likeIntention(id, btn);
    }

    if (e.target.classList.contains('share') || (e.target.closest('.share'))) {
      let btn = e.target.closest('.share');
      let text = btn.getAttribute('data-text');
      if (text && (text.startsWith('"') || text.startsWith("'"))) {
        text = text.slice(1, -1);
      }
      shareIntention(text);
    }
  });
});

function likeIntention(id, btn) {
  fetch('/like/' + id, {method: 'POST'})
    .then(r => r.json())
    .then(data => {
      btn.querySelector('.count').textContent = data.count;
      btn.style.color = data.liked ? '#fc7c46' : '#bbb';
    });
}

function shareIntention(text) {
  var shareText = "🌟 نية من شبكة النوايا:\n" + text + "\nجرب الموقع: https://niya-flask.onrender.com/";
  if (navigator.share) {
    navigator.share({
      title: "شبكة النوايا",
      text: shareText,
      url: window.location.href
    }).catch(() => copyFallback(shareText));
  } else {
    copyFallback(shareText);
  }
}

function copyFallback(txt) {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(txt)
      .then(() => alert("تم نسخ النية بنجاح! شاركها مع أصحابك ❤️"))
      .catch(() => fallbackManual(txt));
  } else {
    fallbackManual(txt);
  }
}

function fallbackManual(txt) {
  var tempInput = document.createElement("textarea");
  tempInput.value = txt;
  document.body.appendChild(tempInput);
  tempInput.select();
  document.execCommand("copy");
  document.body.removeChild(tempInput);
  alert("تم نسخ النية! لو حابة تلصقيها في أي مكان دلوقتي.");
}
