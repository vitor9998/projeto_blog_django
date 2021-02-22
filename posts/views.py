from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView
from posts.models import Post
from django.db.models import Q, Count, Case, When
from comentarios.forms import FormComentario
from comentarios.models import Comentario
from django.contrib import messages
from django.views import View

class PostIndex(ListView):
    model = Post
    template_name = 'posts/index.html'
    paginate_by = 3
    context_object_name = 'posts'

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related('categoria_post') #campo relacionado que eu quero que ele selecione.
        qs = qs.order_by('-id').filter(
            publicado_post=True)  # sem esse filter, desmarcando no admim para não ser publicado, ele continua aparecendo.
        qs = qs.annotate(
            numero_comentarios=Count(  # conta o número de cometarios.
                Case(  # Caso
                    When(comentario__publicado_comentario=True, then=1)
                    # quando. Comentario é um fk deste post e dentro comentário, to procurando
                    # publicado_comentario
                )
            )
        )
        # then=1 --> then conta 1, se for true.
        return qs


class PostBusca(PostIndex):
    template_name = 'posts/post_busca.html'

    def get_queryset(self):
        qs = super().get_queryset()
        termo = self.request.GET.get('termo')

        if not termo:
            return qs

        qs = qs.filter(
            Q(titulo_post__icontains=termo) |
            Q(autor_post__first_name__iexact=termo) |  # não posso usar icontains pq é um fk
            Q(conteudo_post__icontains=termo) |
            Q(excerto_post__icontains=termo) |
            Q(categoria_post__nome_cat__iexact=termo)  # fk
        )

        return qs


class PostCategoria(PostIndex):
    template_name = 'posts/post_categoria.html'

    def get_queryset(self):
        qs = super().get_queryset()

        categoria = self.kwargs.get('categoria', None)  # saber qual categoria a gente está.

        if not categoria:
            return qs

        qs = qs.filter(
            categoria_post__nome_cat__iexact=categoria)  # adicionando um filtro dentro da consulta que ja foi feita no get_queryset

        return qs



#Reescrevemos a classe PostDetalhes, utilizando a View em vez de Updateview.
class PostDetalhes(View):
    template_name= 'posts/post_detalhes.html'


    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        pk = self.kwargs.get('pk')
        post = get_object_or_404(Post, pk=pk, publicado_post=True)
        self.contexto ={
            'post':post,
            'comentarios': Comentario.objects.filter(post_comentario=post,
                                                     publicado_comentario=True),
            'form': FormComentario(request.POST or None),
        }


    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.contexto)

    def post(self, request, *args, **kwargs):
        form = self.contexto['form']

        if not form.is_valid():
            return render(request, self.template_name, self.contexto)

        comentario = form.save(commit=False)

        if request.user.is_authenticated:
            comentario.usuario_comentario = request.user

        comentario.post_comentario = self.contexto['post']
        comentario.save()
        messages.success(request, 'Seu comentário foi enviado para revisão.')
        return redirect('post_detalhes', pk=self.kwargs.get('pk'))

#  To buscando do post categoria_post (models.py), o nome_cat (campo que eu quero utilizar). iexact é o tipo de pesquisa.
# esse i no comeco do iexact é case isensitive, não difere de maiúsculas e minúsculas

# class PostDetalhes(UpdateView):
#     template_name='posts/post_detalhes.html'
#     model = Post
#     form_class = FormComentario
#     context_object_name = 'post'
#
#     def get_context_data(self, **kwargs):
#         contexto = super().get_context_data(**kwargs)
#         post = self.get_object()
#         comentarios = Comentario.objects.filter(publicado_comentario=True,
#                                                 post_comentario=post.id)
#
#         contexto['comentarios'] = comentarios
#
#
#         return contexto
#
#     def form_valid(self, form):
#         post = self.get_object()
#         comentario = Comentario(**form.cleaned_data)
#         comentario.post_comentario = post
#
#         if self.request.user.is_authenticated:  #se o usuario esta logado.
#             comentario.usuario_comentario = self.request.user
#
#         comentario.save()
#         messages.success(self.request, 'Comentário enviado com sucesso.')
#         return redirect('post_detalhes', pk=post.id)


