function submitSearchForm(element){
    var form = document.getElementById("faq-search-form");
    let sentence = element.innerHTML;
    document.getElementById("inputModalSearch").value = sentence;
    form.submit();
}