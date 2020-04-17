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

var toggleModal = function() {
    $('.modal').toggleClass('hidden')
    $('#save_image_url').val('')
}

$('.result a').on('click', function() {
    toggleModal()
    image_url = $(this).parent('.result').attr('data-value')
    $('#save_image_url').val(image_url) 
})

$('.modal .close').on('click', toggleModal)

$('.modal').on('click', function(e) {
    if($(e.target).hasClass('modal')) {
	toggleModal()
    }
})
