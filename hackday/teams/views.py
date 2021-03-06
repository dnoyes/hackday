from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import CreateView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView

from teams.forms import CreateTeamForm, UpdateTeamForm
from teams.forms import UpdateTeamForm
from teams.models import STATUS
from teams.models import Team
from teams.models import TeamCreateStatus


class TeamListView(ListView):
    model = Team
    queryset = Team.objects.filter(status=STATUS.ACTIVE)


class TeamDetailView(DetailView):
    model = Team
    queryset = Team.objects.filter(status=STATUS.ACTIVE)


class TeamUpdateView(UpdateView):
    model = Team
    form_class = UpdateTeamForm
    queryset = Team.objects.filter(status=STATUS.ACTIVE)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """ If user isn't a team member (or team isn't active),
            redirect to team listing.
        """
        try:
            response = super(TeamUpdateView, self).dispatch(*args, **kwargs)
        except:
            return HttpResponseRedirect(reverse('teams-list'))
        if not self.object.is_member(self.request.user):
            return HttpResponseRedirect(reverse('teams-list'))
        return response

    def form_valid(self, form):
        """ In case the user forgets, add the captain as a team member.
        """
        team = form.save()
        team.add_captain_as_member()

        return HttpResponseRedirect(reverse('teams-detail',
            kwargs={'slug': team.slug}))


class TeamCreateView(CreateView):
    model = Team
    form_class = CreateTeamForm

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """ If team creation is disabled (via admin), redirect.
        """
        try:
            online = TeamCreateStatus.objects.all()[0].online
        except:
            online = True

        if online:
            return super(CreateView, self).dispatch(*args, **kwargs)
        else:
            return render(args[0], 'teams/create_offline.html');

    def form_valid(self, form):
        """ Because team doesn't exist in DB yet, and creator is required,
            we need to first save the form, add creator, and THEN save to DB
        """
        team = form.save(commit=False)
        team.status = STATUS.ACTIVE
        team.creator = self.request.user
        team.save()
        form.save_m2m()
        team.add_captain_as_member()

        return HttpResponseRedirect(reverse('teams-detail',
            kwargs={'slug': team.slug}))


def delete_team(request, team_slug):
    try:
        team = Team.objects.get(slug=team_slug)
        if team.is_member(request.user):
            team.status = STATUS.DELETED
            team.save()
            return HttpResponseRedirect(reverse('teams-list'))
        else:
            return HttpResponseRedirect(reverse('teams-detail',
                kwargs={'slug': team_slug}))
    except:
        return HttpResponseRedirect(reverse('teams-detail',
            kwargs={'slug': team_slug}))

