$('.shoe').on('click', function() {
    $('.shoe').removeClass('selected')
    shoe = $(this)
    shoe.addClass('selected')
    $('#shoe_value').val(shoe.attr('data-value'))
    console.log(shoe.attr('data-value'))
})

$('#actions span').on('click', function() {
    button = $(this)
    if (!button.hasClass('bg-blue-400')) {
	$('form').hide()
	$('#'+$(this).attr('data-target')).show()
	$('#actions span').removeClass('bg-gray-400')
	$('#actions span').removeClass('bg-blue-400')
	$('#actions span').addClass('bg-gray-400')
	button.addClass('bg-blue-400')
    }
})

// params = new URLSearchParams(window.location.search)
// if (params.get('image_url')) {
//     shoe = params.get('image_url')
//     $('#shoe_value').val(shoe)
//     $('.shoe[data-value="'+shoe+'"]').addClass('selected')
// }
