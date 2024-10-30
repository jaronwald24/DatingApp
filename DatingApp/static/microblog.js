$(document).ready(function() {
    $('.original').hover(
        function() {
            if (!$(this).find("form.reply-form").length) {

            var link = $("<a>")
                .attr("href", "#")
                .addClass("reply")
                .text("Reply to this post");
            $(this).append(link);

            link.click(function() {
                post_id = parseInt(
                    $(this)
                        .parent()
                        .attr("data-post-id")
                );
                form = create_response_form(post_id);
                $(this).parent().append(form);
                $(this).remove();
            });
            }
        },
        function() {
            $(this).find("a.reply")
                .remove();
        }
    )
});

var create_response_form = function(post_id) {
    var form = $("<form>")
        .attr("method", "post")
        .attr("action", "/new_post")
        .addClass("reply-form");
    var hidden = $("<input>")
        .attr("type", "hidden")
        .attr("name", "response_to")
        .attr("value", post_id);
    var textarea = $("<textarea>")
        .attr("name", "text")
        .attr("placeholder", "Reply to this post");
    var submit = $("<input>")
        .attr("type", "submit")
        .attr("value", "Post");
    var cancel = $("<input>")
        .attr("type", "button")
        .attr("value", "Cancel")
        .click(function() {
           form.remove();
        });
    form.append(hidden)
        .append(textarea)
        .append(submit)
        .append(cancel);
    return form;
}