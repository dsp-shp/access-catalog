import "https://cdnjs.cloudflare.com/ajax/libs/jquery/3.3.1/jquery.min.js";
import "https://cdn.jsdelivr.net/npm/sortablejs@latest/Sortable.min.js";
import "https://cdn.jsdelivr.net/npm/jquery-sortablejs@latest/jquery-sortable.js";

document.addEventListener('DOMContentLoaded', () => {
    Sortable.create(document.querySelector('.sortable'), {
        filter: ".non-draggable",
        preventOnFilter: false,
        animation: 200,
        ghostClass: 'opacity-50',
        onEnd: (evt) => emitEvent(
            "item-drop", {id: parseInt(evt.item.id.slice(1)), new_index: evt.newIndex }
        ),
        onMove: function(evt) {
            return evt.related.className.indexOf('non-draggable') === -1;
        },
    });
});
